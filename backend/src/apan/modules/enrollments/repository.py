from collections.abc import Iterable
from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import AccessScope
from apan.core.pagination import PageParams
from apan.modules.enrollments.models import Enrollment
from apan.modules.enrollments.schemas import EnrollmentFilters, EnrollmentStatus

ACTIVE = EnrollmentStatus.ACTIVE.value


async def get(
    session: AsyncSession, enrollment_id: UUID, *, for_update: bool = False
) -> Enrollment | None:
    statement = select(Enrollment).where(Enrollment.id == enrollment_id)
    if for_update:
        statement = statement.with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def active_for_student_in_year(
    session: AsyncSession, student_id: UUID, school_year_id: UUID
) -> Enrollment | None:
    statement = select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.school_year_id == school_year_id,
        Enrollment.status == ACTIVE,
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def active_for_students(
    session: AsyncSession, student_ids: Iterable[UUID]
) -> list[Enrollment]:
    rows = await session.execute(
        select(Enrollment)
        .where(Enrollment.student_id.in_(list(student_ids)), Enrollment.status == ACTIVE)
        .order_by(Enrollment.starts_on.desc())
    )
    return list(rows.scalars())


async def count_active_in_class(session: AsyncSession, class_id: UUID) -> int:
    statement = select(func.count()).where(
        Enrollment.class_id == class_id, Enrollment.status == ACTIVE
    )
    return (await session.execute(statement)).scalar_one()


async def count_active(session: AsyncSession, class_ids: Iterable[UUID]) -> int:
    statement = select(func.count()).where(
        Enrollment.class_id.in_(list(class_ids)), Enrollment.status == ACTIVE
    )
    return (await session.execute(statement)).scalar_one()


async def student_ids_on(session: AsyncSession, class_id: UUID, on: date) -> list[UUID]:
    """Students whose enrollment in the class covers ``on`` (any status)."""
    rows = await session.execute(
        select(Enrollment.student_id)
        .where(
            Enrollment.class_id == class_id,
            Enrollment.starts_on <= on,
            (Enrollment.ends_on.is_(None)) | (Enrollment.ends_on >= on),
        )
        .distinct()
    )
    return list(rows.scalars())


def active_student_ids(class_ids: Iterable[UUID]) -> Select[UUID]:
    return select(Enrollment.student_id).where(
        Enrollment.class_id.in_(list(class_ids)), Enrollment.status == ACTIVE
    )


async def list_page(
    session: AsyncSession, filters: EnrollmentFilters, scope: AccessScope, page: PageParams
) -> tuple[list[Enrollment], int]:
    statement = select(Enrollment)
    if scope.class_ids is not None:
        statement = statement.where(Enrollment.class_id.in_(scope.class_ids))
    if filters.student_id is not None:
        statement = statement.where(Enrollment.student_id == filters.student_id)
    if filters.class_id is not None:
        statement = statement.where(Enrollment.class_id == filters.class_id)
    if filters.school_year_id is not None:
        statement = statement.where(Enrollment.school_year_id == filters.school_year_id)
    if filters.status is not None:
        statement = statement.where(Enrollment.status == filters.status)
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(Enrollment.starts_on.desc(), Enrollment.id)
        .offset(page.offset)
        .limit(page.limit)
    )
    return list(rows.scalars()), total


def add(session: AsyncSession, enrollment: Enrollment) -> None:
    session.add(enrollment)
