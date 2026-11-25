from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Query, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.config import Settings
from apan.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from apan.core.context import ClientInfo
from apan.core.database import Database
from apan.core.mail import Mailer
from apan.core.pagination import PageParams
from apan.core.rate_limit import RateLimiter


def get_settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


async def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async with database.sessionmaker() as session:
        yield session


def get_redis(request: Request) -> Redis:
    redis: Redis = request.app.state.redis
    return redis


def get_rate_limiter(redis: Annotated[Redis, Depends(get_redis)]) -> RateLimiter:
    return RateLimiter(redis)


def get_mailer(request: Request) -> Mailer:
    mailer: Mailer = request.app.state.mailer
    return mailer


MAX_USER_AGENT_LENGTH = 500


def get_client_info(request: Request) -> ClientInfo:
    user_agent = request.headers.get("user-agent")
    return ClientInfo(
        ip=request.client.host if request.client else None,
        user_agent=user_agent[:MAX_USER_AGENT_LENGTH] if user_agent else None,
    )


def get_page_params(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DatabaseDep = Annotated[Database, Depends(get_database)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
MailerDep = Annotated[Mailer, Depends(get_mailer)]
ClientInfoDep = Annotated[ClientInfo, Depends(get_client_info)]
PageParamsDep = Annotated[PageParams, Depends(get_page_params)]
