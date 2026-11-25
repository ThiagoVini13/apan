from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from apan.core.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_async_engine(
            settings.database_dsn,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "timezone": "UTC",
                    "statement_timeout": str(settings.database_statement_timeout_ms),
                },
            },
        )
        self.sessionmaker = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            autoflush=False,
        )

    async def ping(self) -> None:
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def dispose(self) -> None:
        await self.engine.dispose()


FOREIGN_KEY_VIOLATION = "23503"
UNIQUE_VIOLATION = "23505"


def _cause(exc: IntegrityError) -> object:
    return getattr(exc.orig, "__cause__", None)


def violated_constraint(exc: IntegrityError) -> str | None:
    name = getattr(_cause(exc), "constraint_name", None)
    return str(name) if name else None


def is_foreign_key_violation(exc: IntegrityError) -> bool:
    return getattr(_cause(exc), "sqlstate", None) == FOREIGN_KEY_VIOLATION


def is_unique_violation(exc: IntegrityError) -> bool:
    return getattr(_cause(exc), "sqlstate", None) == UNIQUE_VIOLATION
