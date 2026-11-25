"""Imports every ORM model so ``Base.metadata`` is complete (Alembic, tests)."""


def load_models() -> None:
    import apan.modules.audit.models
    import apan.modules.auth.models
    import apan.modules.classes.models
    import apan.modules.enrollments.models
    import apan.modules.school_years.models
    import apan.modules.students.models
    import apan.modules.subjects.models
    import apan.modules.users.models  # noqa: F401
