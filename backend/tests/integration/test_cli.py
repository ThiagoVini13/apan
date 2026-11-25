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


async def test_seed_demo_builds_a_consistent_dataset(db_session: AsyncSession) -> None:
    from sqlalchemy import func

    from apan.modules.enrollments.models import Enrollment
    from apan.modules.students.models import Student
    from apan.seed import seed_demo

    await auth.create_admin(
        db_session, email="admin@example.com", full_name="Admin", password="a-strong-passphrase"
    )

    result = await seed_demo(db_session, "demo-teacher-passphrase")

    students = await db_session.scalar(select(func.count()).select_from(Student))
    active = await db_session.scalar(
        select(func.count()).select_from(Enrollment).where(Enrollment.status == "active")
    )
    assert result.students == students == active == 15
    # 9 school days between 2026-11-10 and 2026-11-23, 5 lessons per day (2 + 2 + 1 subjects).
    assert result.roll_calls == 9 * 5
