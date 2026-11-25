"""Administrative commands: ``apan --help``."""

import asyncio
from typing import Annotated

import typer

from apan.core.config import get_settings
from apan.core.database import Database
from apan.core.errors import AppError
from apan.models_registry import load_models
from apan.modules.auth import service as auth
from apan.modules.auth.domain import password_problems

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """APAN administrative commands."""


async def _create_admin(email: str, full_name: str, password: str) -> str:
    load_models()
    database = Database(get_settings())
    try:
        async with database.sessionmaker() as session:
            user = await auth.create_admin(
                session, email=email, full_name=full_name, password=password
            )
            return str(user.id)
    finally:
        await database.dispose()


@app.command("create-admin")
def create_admin(
    email: Annotated[str, typer.Option(prompt=True, help="Login e-mail")],
    full_name: Annotated[str, typer.Option("--full-name", prompt=True, help="Full name")],
    password: Annotated[
        str,
        typer.Option(prompt=True, hide_input=True, confirmation_prompt=True, help="Password"),
    ],
) -> None:
    """Create an administrator account (the first one must be created here)."""
    try:
        user_id = asyncio.run(_create_admin(email, full_name.strip(), password))
    except AppError as exc:
        problems = ", ".join(e.code for e in exc.field_errors) or exc.code
        typer.secho(
            f"Could not create the administrator: {problems}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=1) from exc
    typer.secho(f"Administrator created: {user_id}", fg=typer.colors.GREEN)


async def _seed_demo(teacher_password: str) -> str:
    from apan.seed import seed_demo

    load_models()
    database = Database(get_settings())
    try:
        async with database.sessionmaker() as session:
            result = await seed_demo(session, teacher_password)
    finally:
        await database.dispose()
    return (
        f"School year '{result.school_year}' with {result.students} students and "
        f"{result.roll_calls} roll calls. "
        f"Demo teacher: {result.teacher_email}"
    )


@app.command("seed-demo")
def seed_demo(
    teacher_password: Annotated[
        str,
        typer.Option(
            prompt=True,
            hide_input=True,
            confirmation_prompt=True,
            help="Password for the demo teacher account",
        ),
    ],
) -> None:
    """Fill a development database with synthetic demo data."""
    if get_settings().is_production:
        typer.secho("seed-demo is disabled in production.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    problems = password_problems(teacher_password, "professora.demo@example.com")
    if problems:
        typer.secho(f"Weak password: {', '.join(problems)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    try:
        message = asyncio.run(_seed_demo(teacher_password))
    except AppError as exc:
        typer.secho(f"Could not seed: {exc.code}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.secho(message, fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
