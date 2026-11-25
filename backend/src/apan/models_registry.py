"""Imports every ORM model so ``Base.metadata`` is complete (Alembic, tests)."""


def load_models() -> None:
    import apan.modules.audit.models
    import apan.modules.auth.models
    import apan.modules.users.models  # noqa: F401
