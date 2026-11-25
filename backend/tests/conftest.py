from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from apan.core.config import Environment, Settings
from apan.main import create_app

UNREACHABLE_DATABASE_URL = "postgresql+asyncpg://apan:apan@127.0.0.1:1/apan"
UNREACHABLE_REDIS_URL = "redis://127.0.0.1:1/0"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": Environment.TEST,
        "database_url": UNREACHABLE_DATABASE_URL,
        "redis_url": UNREACHABLE_REDIS_URL,
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings.model_validate(values)


@pytest.fixture
def settings() -> Settings:
    """Settings pointing to unreachable services: enough for tests without I/O."""
    return make_settings()


async def _client_for(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
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


@pytest.fixture
def integration_settings(postgres_url: str, redis_url: str) -> Settings:
    return make_settings(database_url=postgres_url, redis_url=redis_url)


@pytest.fixture
async def integration_client(integration_settings: Settings) -> AsyncIterator[AsyncClient]:
    async for c in _client_for(create_app(integration_settings)):
        yield c


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/integration" in item.path.as_posix():
            item.add_marker(pytest.mark.integration)
