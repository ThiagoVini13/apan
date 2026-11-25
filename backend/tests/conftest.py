from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from apan.core.config import Environment, Settings
from apan.core.mail import Mail
from apan.main import create_app

if TYPE_CHECKING:
    from tests.factories.registries import Seed

BACKEND_DIR = Path(__file__).resolve().parents[1]
UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://apan:apan@127.0.0.1:1/apan"
UNREACHABLE_REDIS_URL = "redis://127.0.0.1:1/0"
TEST_ORIGIN = "http://test"
TEST_SECRET_KEY = "test-secret-key-with-more-than-32-characters"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": Environment.TEST,
        "secret_key": TEST_SECRET_KEY,
        "database_url": UNREACHABLE_DATABASE_URL,
        "redis_url": UNREACHABLE_REDIS_URL,
        "log_level": "WARNING",
        "cors_origins": [TEST_ORIGIN],
        "frontend_url": TEST_ORIGIN,
        "refresh_cookie_secure": False,
    }
    values.update(overrides)
    return Settings.model_validate(values)


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[Mail] = []

    def send(self, mail: Mail) -> None:
        self.sent.append(mail)


@pytest.fixture
def settings() -> Settings:
    """Settings pointing to unreachable services: enough for tests without I/O."""
    return make_settings()


async def _client_for(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url=TEST_ORIGIN) as client:
        yield client
    await app.state.redis.aclose()
    await app.state.database.dispose()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async for c in _client_for(app):
        yield c


# --------------------------------------------------------------------------- containers


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    from testcontainers.community.postgres import PostgresContainer

    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as container:
        yield container.get_connection_url()


@pytest.fixture(scope="session")
def redis_url() -> Iterator[str]:
    from testcontainers.community.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as container:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(container.port)
        yield f"redis://{host}:{port}/0"


def alembic_config(database_url: str) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["database_url"] = database_url
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session")
def migrated_postgres_url(postgres_url: str) -> str:
    command.upgrade(alembic_config(postgres_url), "head")
    return postgres_url


@pytest.fixture
async def db_connection(migrated_postgres_url: str) -> AsyncIterator[AsyncConnection]:
    """One connection per test inside a transaction that is rolled back at the end."""
    engine = create_async_engine(migrated_postgres_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        yield connection
        await transaction.rollback()
    await engine.dispose()


def _sessionmaker(connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
    # Service commits become savepoint releases inside the outer test transaction.
    return async_sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    async with _sessionmaker(db_connection)() as session:
        yield session


@pytest.fixture
async def redis_client(redis_url: str) -> AsyncIterator[Redis]:
    redis = Redis.from_url(redis_url, decode_responses=True)
    await redis.flushdb()
    yield redis
    await redis.aclose()


@pytest.fixture
def integration_settings(migrated_postgres_url: str, redis_url: str) -> Settings:
    return make_settings(database_url=migrated_postgres_url, redis_url=redis_url)


@pytest.fixture
def mailer() -> FakeMailer:
    return FakeMailer()


@pytest.fixture
def integration_app(
    integration_settings: Settings,
    db_connection: AsyncConnection,
    redis_client: Redis,
    mailer: FakeMailer,
) -> FastAPI:
    app = create_app(integration_settings)
    app.state.database.sessionmaker = _sessionmaker(db_connection)
    app.state.mailer = mailer
    return app


@pytest.fixture
async def api(integration_app: FastAPI) -> AsyncIterator[AsyncClient]:
    async for c in _client_for(integration_app):
        yield c


@pytest.fixture
async def integration_client(integration_settings: Settings) -> AsyncIterator[AsyncClient]:
    """Real engine and pool (no transaction override), for infrastructure checks."""
    async for c in _client_for(create_app(integration_settings)):
        yield c


@pytest.fixture
async def seed(api: AsyncClient, db_session: AsyncSession) -> "Seed":
    from tests.factories.registries import make_seed

    return await make_seed(api, db_session)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        path = item.path.as_posix()
        if "tests/integration" in path or "tests/security" in path:
            item.add_marker(pytest.mark.integration)
