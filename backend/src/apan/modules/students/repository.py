from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.pagination import PageParams
from apan.modules.students.models import ENROLLMENT_NUMBER_SEQUENCE, Guardian, Student


async def get(
    session: AsyncSession, student_id: UUID, *, for_update: bool = False
) -> Student | None:
    statement = select(Student).where(Student.id == student_id)
    if for_update:
        statement = statement.with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def get_many(session: AsyncSession, ids: list[UUID]) -> list[Student]:
    rows = await session.execute(select(Student).where(Student.id.in_(ids)))
    return list(rows.scalars())


async def is_within(session: AsyncSession, student_id: UUID, allowed: Select[UUID]) -> bool:
    statement = select(Student.id).where(Student.id == student_id, Student.id.in_(allowed))
    return (await session.execute(statement)).first() is not None


async def list_page(
    session: AsyncSession,
    *,
    q: str | None,
    allowed: Select[UUID] | None,
    include_archived: bool,
    page: PageParams,
) -> tuple[list[Student], int]:
    statement = select(Student)
    if allowed is not None:
        statement = statement.where(Student.id.in_(allowed))
    if not include_archived:
        statement = statement.where(Student.archived_at.is_(None))
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            or_(Student.full_name.ilike(pattern), Student.enrollment_number.ilike(pattern))
        )
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(Student.full_name, Student.id).offset(page.offset).limit(page.limit)
    )
    return list(rows.scalars()), total


async def next_enrollment_sequence(session: AsyncSession) -> int:
    value = await session.scalar(ENROLLMENT_NUMBER_SEQUENCE.next_value())
    return int(value)


async def list_guardians(session: AsyncSession, student_id: UUID) -> list[Guardian]:
    rows = await session.execute(
        select(Guardian)
        .where(Guardian.student_id == student_id)
        .order_by(Guardian.is_primary.desc(), Guardian.full_name, Guardian.id)
    )
    return list(rows.scalars())


async def get_guardian(
    session: AsyncSession, student_id: UUID, guardian_id: UUID
) -> Guardian | None:
    statement = select(Guardian).where(
        Guardian.id == guardian_id, Guardian.student_id == student_id
    )
    return (await session.execute(statement)).scalar_one_or_none()


def add(session: AsyncSession, entity: Student | Guardian) -> None:
    session.add(entity)


async def delete(session: AsyncSession, entity: Guardian) -> None:
    await session.delete(entity)
