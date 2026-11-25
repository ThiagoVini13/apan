from datetime import date
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.pagination import PageParams
from apan.modules.school_years.models import CalendarDay, SchoolYear, Term


async def get(session: AsyncSession, year_id: UUID) -> SchoolYear | None:
    return await session.get(SchoolYear, year_id)


async def name_exists(session: AsyncSession, name: str, *, exclude_id: UUID | None = None) -> bool:
    statement = select(SchoolYear.id).where(func.lower(SchoolYear.name) == name.lower())
    if exclude_id is not None:
        statement = statement.where(SchoolYear.id != exclude_id)
    return (await session.execute(statement.limit(1))).first() is not None


async def list_page(session: AsyncSession, page: PageParams) -> tuple[list[SchoolYear], int]:
    total = (await session.execute(select(func.count()).select_from(SchoolYear))).scalar_one()
    rows = await session.execute(
        select(SchoolYear)
        .order_by(SchoolYear.starts_on.desc(), SchoolYear.id)
        .offset(page.offset)
        .limit(page.limit)
    )
    return list(rows.scalars()), total


async def clear_current(session: AsyncSession, *, except_id: UUID | None = None) -> None:
    statement = update(SchoolYear).where(SchoolYear.is_current.is_(True))
    if except_id is not None:
        statement = statement.where(SchoolYear.id != except_id)
    await session.execute(statement.values(is_current=False))


async def get_current(session: AsyncSession) -> SchoolYear | None:
    statement = select(SchoolYear).where(SchoolYear.is_current.is_(True))
    return (await session.execute(statement)).scalar_one_or_none()


async def list_terms(session: AsyncSession, year_id: UUID) -> list[Term]:
    rows = await session.execute(
        select(Term).where(Term.school_year_id == year_id).order_by(Term.starts_on)
    )
    return list(rows.scalars())


async def get_term(session: AsyncSession, year_id: UUID, term_id: UUID) -> Term | None:
    statement = select(Term).where(Term.id == term_id, Term.school_year_id == year_id)
    return (await session.execute(statement)).scalar_one_or_none()


async def list_calendar_days(
    session: AsyncSession, year_id: UUID, *, start: date | None = None, end: date | None = None
) -> list[CalendarDay]:
    statement = select(CalendarDay).where(CalendarDay.school_year_id == year_id)
    if start is not None:
        statement = statement.where(CalendarDay.day >= start)
    if end is not None:
        statement = statement.where(CalendarDay.day <= end)
    rows = await session.execute(statement.order_by(CalendarDay.day))
    return list(rows.scalars())


async def get_calendar_day(
    session: AsyncSession, year_id: UUID, day_id: UUID
) -> CalendarDay | None:
    statement = select(CalendarDay).where(
        CalendarDay.id == day_id, CalendarDay.school_year_id == year_id
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def calendar_day_exists(session: AsyncSession, year_id: UUID, day: date) -> bool:
    statement = select(CalendarDay.id).where(
        CalendarDay.school_year_id == year_id, CalendarDay.day == day
    )
    return (await session.execute(statement.limit(1))).first() is not None


def add(session: AsyncSession, entity: SchoolYear | Term | CalendarDay) -> None:
    session.add(entity)


async def delete(session: AsyncSession, entity: SchoolYear | Term | CalendarDay) -> None:
    await session.delete(entity)
