from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import ScalarSelect, Select, String, Uuid, column, delete, func, or_, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import AccessScope
from apan.core.pagination import PageParams
from apan.modules.classes.models import ClassSubjectTeacher, SchoolClass
from apan.modules.classes.schemas import ClassFilters

# Lightweight reference to the enrollments table (owned by the enrollments module)
# for counting students without importing its ORM model.
_enrollments = table("enrollments", column("class_id", Uuid), column("status", String))


def _student_count() -> ScalarSelect[int]:
    return (
        select(func.count())
        .select_from(_enrollments)
        .where(_enrollments.c.class_id == SchoolClass.id, _enrollments.c.status == "active")
        .scalar_subquery()
    )


def _with_count() -> Select[SchoolClass, int]:
    return select(SchoolClass, _student_count())


def _scoped(statement: Select[SchoolClass, int], scope: AccessScope) -> Select[SchoolClass, int]:
    if scope.class_ids is not None:
        statement = statement.where(SchoolClass.id.in_(scope.class_ids))
    return statement


async def get(
    session: AsyncSession, class_id: UUID, *, for_update: bool = False
) -> SchoolClass | None:
    statement = select(SchoolClass).where(SchoolClass.id == class_id)
    if for_update:
        statement = statement.with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def get_with_count(
    session: AsyncSession, class_id: UUID, scope: AccessScope
) -> tuple[SchoolClass, int] | None:
    statement = _scoped(_with_count().where(SchoolClass.id == class_id), scope)
    row = (await session.execute(statement)).first()
    return (row[0], int(row[1])) if row else None


async def get_many(session: AsyncSession, ids: Iterable[UUID]) -> list[SchoolClass]:
    rows = await session.execute(select(SchoolClass).where(SchoolClass.id.in_(list(ids))))
    return list(rows.scalars())


async def count_active_students(session: AsyncSession, class_id: UUID) -> int:
    statement = (
        select(func.count())
        .select_from(_enrollments)
        .where(_enrollments.c.class_id == class_id, _enrollments.c.status == "active")
    )
    return (await session.execute(statement)).scalar_one()


async def list_page(
    session: AsyncSession, filters: ClassFilters, scope: AccessScope, page: PageParams
) -> tuple[list[tuple[SchoolClass, int]], int]:
    statement = _scoped(_with_count(), scope)
    if filters.school_year_id is not None:
        statement = statement.where(SchoolClass.school_year_id == filters.school_year_id)
    if filters.shift is not None:
        statement = statement.where(SchoolClass.shift == filters.shift)
    if filters.is_active is not None:
        statement = statement.where(SchoolClass.is_active.is_(filters.is_active))
    if filters.q:
        pattern = f"%{filters.q.strip()}%"
        statement = statement.where(
            or_(SchoolClass.name.ilike(pattern), SchoolClass.grade.ilike(pattern))
        )
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(SchoolClass.name, SchoolClass.shift, SchoolClass.id)
        .offset(page.offset)
        .limit(page.limit)
    )
    return [(row[0], int(row[1])) for row in rows], total


async def name_taken(
    session: AsyncSession,
    school_year_id: UUID,
    name: str,
    shift: str,
    *,
    exclude_id: UUID | None = None,
) -> bool:
    statement = select(SchoolClass.id).where(
        SchoolClass.school_year_id == school_year_id,
        func.lower(SchoolClass.name) == name.lower(),
        SchoolClass.shift == shift,
    )
    if exclude_id is not None:
        statement = statement.where(SchoolClass.id != exclude_id)
    return (await session.execute(statement.limit(1))).first() is not None


async def class_ids_for_teacher(session: AsyncSession, teacher_id: UUID) -> frozenset[UUID]:
    rows = await session.execute(
        select(ClassSubjectTeacher.class_id).where(ClassSubjectTeacher.teacher_id == teacher_id)
    )
    return frozenset(rows.scalars())


async def list_assignments(session: AsyncSession, class_id: UUID) -> list[ClassSubjectTeacher]:
    rows = await session.execute(
        select(ClassSubjectTeacher).where(ClassSubjectTeacher.class_id == class_id)
    )
    return list(rows.scalars())


async def replace_assignments(
    session: AsyncSession, class_id: UUID, pairs: list[tuple[UUID, UUID]]
) -> None:
    await session.execute(
        delete(ClassSubjectTeacher).where(ClassSubjectTeacher.class_id == class_id)
    )
    session.add_all(
        ClassSubjectTeacher(class_id=class_id, subject_id=subject_id, teacher_id=teacher_id)
        for subject_id, teacher_id in pairs
    )


def add(session: AsyncSession, school_class: SchoolClass) -> None:
    session.add(school_class)
