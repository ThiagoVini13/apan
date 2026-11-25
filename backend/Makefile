.PHONY: install dev lint format typecheck test test-unit migrate revision audit openapi check

install:
	uv sync

dev:
	uv run uvicorn --factory apan.main:create_app --reload --reload-dir src

lint:
	uv run ruff check src tests migrations
	uv run ruff format --check src tests migrations
	uv run lint-imports

format:
	uv run ruff format src tests migrations
	uv run ruff check --fix src tests migrations

typecheck:
	uv run mypy

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

migrate:
	uv run alembic upgrade head

revision:
	uv run alembic revision --autogenerate -m "$(m)"

openapi:
	uv run python -m scripts.export_openapi

audit:
	uv run pip-audit

check: lint typecheck test
