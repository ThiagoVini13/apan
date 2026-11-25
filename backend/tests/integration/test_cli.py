import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from apan import cli
from apan.core.errors import ConflictError
from apan.modules.auth import service as auth
from apan.modules.users.models import User


async def test_create_admin_service_creates_active_admin(db_session: AsyncSession) -> None:
    user = await auth.create_admin(
        db_session,
        email="Diretora@Example.com",
        full_name="Diretora",
        password="a-strong-passphrase",
    )

    stored = (await db_session.execute(select(User).where(User.id == user.id))).scalar_one()
    assert (stored.email, stored.role, stored.must_change_password) == (
        "diretora@example.com",
        "admin",
        False,
    )


async def test_create_admin_rejects_duplicate_email(db_session: AsyncSession) -> None:
    await auth.create_admin(
        db_session, email="dup@example.com", full_name="A", password="a-strong-passphrase"
    )

    with pytest.raises(ConflictError):
        await auth.create_admin(
            db_session, email="DUP@example.com", full_name="B", password="a-strong-passphrase"
        )


def test_cli_reports_weak_password(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake(email: str, full_name: str, password: str) -> str:
        from apan.modules.auth.service import _check_password_policy

        _check_password_policy(password, email, field="password")
        return "unused"

    monkeypatch.setattr(cli, "_create_admin", fake)

    result = CliRunner().invoke(
        cli.app,
        [
            "create-admin",
            "--email",
            "a@example.com",
            "--full-name",
            "A",
            "--password",
            "1234567890",
        ],
    )

    assert result.exit_code == 1
    assert "password_too_common" in result.output
