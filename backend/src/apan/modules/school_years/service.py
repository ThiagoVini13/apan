from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Actor, ClientInfo
from apan.core.database import is_foreign_key_violation
from apan.core.errors import ConflictError, FieldError, NotFoundError, ValidationError
from apan.core.pagination import ItemList, Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.school_years import domain, repository
from apan.modules.school_years.models import CalendarDay, SchoolYear, Term
from apan.modules.school_years.schemas import (
    CalendarDayCreate,
    CalendarDayRead,
    SchoolYearCreate,
    SchoolYearRead,
    SchoolYearUpdate,
    TermCreate,
    TermRead,
)


def _year_not_found() -> NotFoundError:
    return NotFoundError(code="school_year_not_found")


def _invalid_dates(field: str = "endsOn") -> ValidationError:
    return ValidationError(
        code="invalid_date_range", field_errors=[FieldError(field=field, code="invalid_date_range")]
    )


def _outside_year(field: str) -> ValidationError:
    return ValidationError(
        code="date_outside_school_year",
        field_errors=[FieldError(field=field, code="date_outside_school_year")],
    )


async def _get_year(session: AsyncSession, year_id: UUID) -> SchoolYear:
    year = await repository.get(session, year_id)
    if year is None:
        raise _year_not_found()
    return year


# --------------------------------------------------------------------------- public helpers


async def find_year(session: AsyncSession, year_id: UUID) -> SchoolYearRead | None:
    year = await repository.get(session, year_id)
    return SchoolYearRead.model_validate(year) if year else None


async def current_year(session: AsyncSession) -> SchoolYearRead | None:
    year = await repository.get_current(session)
    return SchoolYearRead.model_validate(year) if year else None


async def school_days(session: AsyncSession, year_id: UUID, start: date, end: date) -> list[date]:
    """School days between start and end, clipped to the school year."""
    year = await _get_year(session, year_id)
    start, end = max(start, year.starts_on), min(end, year.ends_on)
    if start > end:
        return []
    special = await repository.list_calendar_days(session, year_id, start=start, end=end)
    return domain.school_days(start, end, [(d.day, d.kind) for d in special])


# --------------------------------------------------------------------------- school years


async def list_years(session: AsyncSession, page: PageParams) -> Page[SchoolYearRead]:
    years, total = await repository.list_page(session, page)
    return Page[SchoolYearRead].build(
        [SchoolYearRead.model_validate(y) for y in years], total, page
    )


async def get_year(session: AsyncSession, year_id: UUID) -> SchoolYearRead:
    return SchoolYearRead.model_validate(await _get_year(session, year_id))


async def _ensure_unique_name(
    session: AsyncSession, name: str, exclude_id: UUID | None = None
) -> None:
    if await repository.name_exists(session, name, exclude_id=exclude_id):
        raise ConflictError(
            code="school_year_name_taken",
            field_errors=[FieldError(field="name", code="school_year_name_taken")],
        )


async def create_year(
    session: AsyncSession, actor: Actor, data: SchoolYearCreate, client: ClientInfo
) -> SchoolYearRead:
    if data.ends_on <= data.starts_on:
        raise _invalid_dates()
    await _ensure_unique_name(session, data.name)
    if data.is_current:
        await repository.clear_current(session)
    year = SchoolYear(
        name=data.name, starts_on=data.starts_on, ends_on=data.ends_on, is_current=data.is_current
    )
    repository.add(session, year)
    await session.flush()
    audit.record(
        session,
        "school_years.created",
        client=client,
        actor_id=actor.user_id,
        entity_type="school_year",
        entity_id=year.id,
    )
    await session.commit()
    return SchoolYearRead.model_validate(year)


async def update_year(
    session: AsyncSession, actor: Actor, year_id: UUID, data: SchoolYearUpdate, client: ClientInfo
) -> SchoolYearRead:
    year = await _get_year(session, year_id)
    if data.name is not None and data.name != year.name:
        await _ensure_unique_name(session, data.name, exclude_id=year.id)
        year.name = data.name
    starts_on = data.starts_on or year.starts_on
    ends_on = data.ends_on or year.ends_on
    if ends_on <= starts_on:
        raise _invalid_dates()
    for term in await repository.list_terms(session, year.id):
        if not domain.within(term.starts_on, term.ends_on, starts_on, ends_on):
            raise ConflictError(code="terms_outside_school_year")
    year.starts_on, year.ends_on = starts_on, ends_on
    if data.is_current is True and not year.is_current:
        await repository.clear_current(session, except_id=year.id)
        await session.flush()
    if data.is_current is not None:
        year.is_current = data.is_current
    audit.record(
        session,
        "school_years.updated",
        client=client,
        actor_id=actor.user_id,
        entity_type="school_year",
        entity_id=year.id,
        details={"fields": sorted(data.model_fields_set)},
    )
    await session.commit()
    await session.refresh(year)
    return SchoolYearRead.model_validate(year)


async def delete_year(
    session: AsyncSession, actor: Actor, year_id: UUID, client: ClientInfo
) -> None:
    year = await _get_year(session, year_id)
    await repository.delete(session, year)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        if is_foreign_key_violation(exc):
            raise ConflictError(code="school_year_in_use") from exc
        raise
    audit.record(
        session,
        "school_years.deleted",
        client=client,
        actor_id=actor.user_id,
        entity_type="school_year",
        entity_id=year_id,
    )
    await session.commit()


# --------------------------------------------------------------------------- terms


async def list_terms(session: AsyncSession, year_id: UUID) -> ItemList[TermRead]:
    await _get_year(session, year_id)
    terms = await repository.list_terms(session, year_id)
    return ItemList[TermRead].of([TermRead.model_validate(t) for t in terms])


async def create_term(
    session: AsyncSession, actor: Actor, year_id: UUID, data: TermCreate, client: ClientInfo
) -> TermRead:
    year = await _get_year(session, year_id)
    if data.ends_on < data.starts_on:
        raise _invalid_dates()
    if not domain.within(data.starts_on, data.ends_on, year.starts_on, year.ends_on):
        raise _outside_year("startsOn")
    for term in await repository.list_terms(session, year_id):
        if term.name.lower() == data.name.lower():
            raise ConflictError(
                code="term_name_taken", field_errors=[FieldError("name", "term_name_taken")]
            )
        if domain.overlaps(data.starts_on, data.ends_on, term.starts_on, term.ends_on):
            raise ConflictError(code="term_overlaps")
    term = Term(
        school_year_id=year_id, name=data.name, starts_on=data.starts_on, ends_on=data.ends_on
    )
    repository.add(session, term)
    await session.flush()
    audit.record(
        session,
        "terms.created",
        client=client,
        actor_id=actor.user_id,
        entity_type="term",
        entity_id=term.id,
    )
    await session.commit()
    return TermRead.model_validate(term)


async def delete_term(
    session: AsyncSession, actor: Actor, year_id: UUID, term_id: UUID, client: ClientInfo
) -> None:
    term = await repository.get_term(session, year_id, term_id)
    if term is None:
        raise NotFoundError(code="term_not_found")
    await repository.delete(session, term)
    audit.record(
        session,
        "terms.deleted",
        client=client,
        actor_id=actor.user_id,
        entity_type="term",
        entity_id=term_id,
    )
    await session.commit()


# --------------------------------------------------------------------------- calendar days


async def list_calendar_days(session: AsyncSession, year_id: UUID) -> ItemList[CalendarDayRead]:
    await _get_year(session, year_id)
    days = await repository.list_calendar_days(session, year_id)
    return ItemList[CalendarDayRead].of([CalendarDayRead.model_validate(d) for d in days])


async def create_calendar_day(
    session: AsyncSession, actor: Actor, year_id: UUID, data: CalendarDayCreate, client: ClientInfo
) -> CalendarDayRead:
    year = await _get_year(session, year_id)
    if not domain.within(data.day, data.day, year.starts_on, year.ends_on):
        raise _outside_year("day")
    if await repository.calendar_day_exists(session, year_id, data.day):
        raise ConflictError(
            code="calendar_day_taken", field_errors=[FieldError("day", "calendar_day_taken")]
        )
    day = CalendarDay(
        school_year_id=year_id, day=data.day, kind=data.kind, description=data.description
    )
    repository.add(session, day)
    await session.flush()
    audit.record(
        session,
        "calendar_days.created",
        client=client,
        actor_id=actor.user_id,
        entity_type="calendar_day",
        entity_id=day.id,
    )
    await session.commit()
    return CalendarDayRead.model_validate(day)


async def delete_calendar_day(
    session: AsyncSession, actor: Actor, year_id: UUID, day_id: UUID, client: ClientInfo
) -> None:
    day = await repository.get_calendar_day(session, year_id, day_id)
    if day is None:
        raise NotFoundError(code="calendar_day_not_found")
    await repository.delete(session, day)
    audit.record(
        session,
        "calendar_days.deleted",
        client=client,
        actor_id=actor.user_id,
        entity_type="calendar_day",
        entity_id=day_id,
    )
    await session.commit()
