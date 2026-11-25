import asyncio
from collections.abc import Awaitable

import structlog
from redis.asyncio import Redis

from apan.core.database import Database

READINESS_TIMEOUT_SECONDS = 3.0

_logger = structlog.get_logger("apan.health")


async def _check(name: str, probe: Awaitable[object]) -> bool:
    try:
        async with asyncio.timeout(READINESS_TIMEOUT_SECONDS):
            await probe
    except Exception as exc:
        _logger.warning("dependency_unavailable", dependency=name, error=type(exc).__name__)
        return False
    return True


async def is_ready(database: Database, redis: Redis) -> bool:
    results = await asyncio.gather(
        _check("database", database.ping()),
        _check("redis", redis.ping()),
    )
    return all(results)
