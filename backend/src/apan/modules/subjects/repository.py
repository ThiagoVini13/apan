from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.pagination import PageParams
from apan.modules.subjects.models import Subject


async def get(session: AsyncSession, subject_id: UUID) -> Subject | None:
    return await session.get(Subject, subject_id)


async def get_many(session: AsyncSession, ids: Iterable[UUID]) -> list[Subject]:
    rows = await session.execute(select(Subject).where(Subject.id.in_(list(ids))))
    return list(rows.scalars())


async def code_exists(session: AsyncSession, code: str, *, exclude_id: UUID | None = None) -> bool:
    statement = select(Subject.id).where(Subject.code == code)
    if exclude_id is not None:
        statement = statement.where(Subject.id != exclude_id)
    return (await session.execute(statement.limit(1))).first() is not None


async def list_page(
    session: AsyncSession, q: str | None, page: PageParams
) -> tuple[list[Subject], int]:
    statement = select(Subject)
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(or_(Subject.name.ilike(pattern), Subject.code.ilike(pattern)))
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(Subject.name, Subject.id).offset(page.offset).limit(page.limit)
    )
    return list(rows.scalars()), total


def add(session: AsyncSession, subject: Subject) -> None:
    session.add(subject)


async def delete(session: AsyncSession, subject: Subject) -> None:
    await session.delete(subject)
