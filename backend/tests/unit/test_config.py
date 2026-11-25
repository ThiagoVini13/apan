import pytest
from pydantic import ValidationError

from apan.core.config import Environment
from tests.conftest import make_settings


def test_production_rejects_default_secret_key() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        make_settings(app_env=Environment.PRODUCTION)


def test_production_rejects_short_secret_key() -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        make_settings(app_env=Environment.PRODUCTION, secret_key="short-but-not-default")


def test_production_disables_docs() -> None:
    settings = make_settings(app_env=Environment.PRODUCTION, secret_key="x" * 40)

    assert settings.docs_enabled is False


def test_cors_origins_accept_comma_separated_string() -> None:
    settings = make_settings(cors_origins="http://a.test, http://b.test")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_database_dsn_is_built_and_escaped() -> None:
    settings = make_settings(database_url=None, postgres_host="db", postgres_password="p@ss:w/rd")

    assert settings.database_dsn == "postgresql+asyncpg://apan:p%40ss%3Aw%2Frd@db:5432/apan"


def test_production_rejects_default_database_password() -> None:
    with pytest.raises(ValidationError, match="POSTGRES_PASSWORD"):
        make_settings(app_env=Environment.PRODUCTION, secret_key="x" * 40, database_url=None)
