"""Fixed-window rate limiting on Redis.

Fails open: if Redis is unavailable the request goes through and a warning is
logged, so an outage does not lock everyone out of the login.
"""

from dataclasses import dataclass

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from apan.core.errors import RateLimitError

_logger = structlog.get_logger("apan.rate_limit")


@dataclass(frozen=True, slots=True)
class Rate:
    limit: int
    window_seconds: int


class RateLimiter:
    def __init__(self, redis: Redis, prefix: str = "ratelimit") -> None:
        self._redis = redis
        self._prefix = prefix

    async def hit(self, scope: str, identifier: str, rate: Rate) -> None:
        """Counts one hit; raises ``RateLimitError`` once the limit is exceeded."""
        key = f"{self._prefix}:{scope}:{identifier}"
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, rate.window_seconds, nx=True)
                pipe.ttl(key)
                count, _, ttl = await pipe.execute()
        except RedisError as exc:
            _logger.warning("rate_limit_unavailable", scope=scope, error=type(exc).__name__)
            return
        if int(count) > rate.limit:
            retry_after = max(int(ttl), 1)
            raise RateLimitError(
                f"Rate limit exceeded for {scope}.",
                headers={"Retry-After": str(retry_after)},
            )

    async def reset(self, scope: str, identifier: str) -> None:
        try:
            await self._redis.delete(f"{self._prefix}:{scope}:{identifier}")
        except RedisError as exc:
            _logger.warning("rate_limit_unavailable", scope=scope, error=type(exc).__name__)
