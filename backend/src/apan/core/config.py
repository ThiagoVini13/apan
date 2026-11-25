from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

INSECURE_SECRET_KEYS = frozenset({"", "change-me", "change-me-in-production"})


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Repository root first, then backend/ (later files win).
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Environment = Environment.DEVELOPMENT
    secret_key: SecretStr = SecretStr("change-me")
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "apan"
    postgres_password: SecretStr = SecretStr("apan")
    postgres_db: str = "apan"
    # Full URL override; when unset the URL is built from the POSTGRES_* values.
    database_url: str | None = None
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_pool_timeout: float = Field(default=10.0, gt=0)
    database_statement_timeout_ms: int = Field(default=15_000, ge=0)

    redis_url: str = "redis://localhost:6379/0"

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _check_production(self) -> Self:
        if self.is_production:
            if self.secret_key.get_secret_value() in INSECURE_SECRET_KEYS:
                raise ValueError("SECRET_KEY must be set to a strong value in production")
            if len(self.secret_key.get_secret_value()) < 32:
                raise ValueError("SECRET_KEY must have at least 32 characters in production")
            if self.database_url is None and self.postgres_password.get_secret_value() == "apan":
                raise ValueError("POSTGRES_PASSWORD must be changed in production")
        return self

    @property
    def database_dsn(self) -> str:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        ).render_as_string(hide_password=False)

    @property
    def is_production(self) -> bool:
        return self.app_env is Environment.PRODUCTION

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()
