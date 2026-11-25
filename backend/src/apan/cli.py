"""Administrative commands: ``apan --help``."""

import asyncio
from typing import Annotated

import typer

from apan.core.config import get_settings
from apan.core.database import Database
from apan.core.errors import AppError
from apan.models_registry import load_models
from apan.modules.auth import service as auth

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


if __name__ == "__main__":
    app()
