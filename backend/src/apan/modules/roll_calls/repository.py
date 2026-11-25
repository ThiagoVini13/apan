from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy import Select, delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import AccessScope
from apan.core.pagination import PageParams
from apan.modules.roll_calls.models import AttendanceRecord, RollCall
from apan.modules.roll_calls.schemas import AttendanceQuery, RollCallFilters

_PRESENT = func.count().filter(AttendanceRecord.status == "present")
_ABSENT = func.count().filter(AttendanceRecord.status == "absent")


def _counts() -> tuple[Any, Any]:
    present = (
        select(func.count())
        .where(AttendanceRecord.roll_call_id == RollCall.id, AttendanceRecord.status == "present")
        .scalar_subquery()
    )
    absent = (
        select(func.count())
        .where(AttendanceRecord.roll_call_id == RollCall.id, AttendanceRecord.status == "absent")
        .scalar_subquery()
    )
    return present, absent


async def get(session: AsyncSession, roll_call_id: UUID) -> RollCall | None:
    return await session.get(RollCall, roll_call_id)


async def get_by_key(
    session: AsyncSession,
    class_id: UUID,
    subject_id: UUID,
    lesson_date: date,
    *,
    for_update: bool = False,
) -> RollCall | None:
    statement = select(RollCall).where(
        RollCall.class_id == class_id,
        RollCall.subject_id == subject_id,
        RollCall.lesson_date == lesson_date,
    )
    if for_update:
        statement = statement.with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def records_for(session: AsyncSession, roll_call_id: UUID) -> list[AttendanceRecord]:
    rows = await session.execute(
        select(AttendanceRecord).where(AttendanceRecord.roll_call_id == roll_call_id)
    )
    return list(rows.scalars())


async def replace_records(
    session: AsyncSession, roll_call_id: UUID, marks: list[tuple[UUID, str]]
) -> None:
    await session.execute(
        delete(AttendanceRecord).where(AttendanceRecord.roll_call_id == roll_call_id)
    )
    if marks:
        await session.execute(
            insert(AttendanceRecord),
            [
                {"roll_call_id": roll_call_id, "student_id": student_id, "status": status}
                for student_id, status in marks
            ],
        )


async def list_page(
    session: AsyncSession, filters: RollCallFilters, scope: AccessScope, page: PageParams
) -> tuple[list[tuple[RollCall, int, int]], int]:
    present, absent = _counts()
    statement: Select[Any] = select(RollCall, present, absent)
    if scope.class_ids is not None:
        statement = statement.where(RollCall.class_id.in_(scope.class_ids))
    if filters.class_id is not None:
        statement = statement.where(RollCall.class_id == filters.class_id)
    if filters.subject_id is not None:
        statement = statement.where(RollCall.subject_id == filters.subject_id)
    if filters.lesson_date is not None:
        statement = statement.where(RollCall.lesson_date == filters.lesson_date)
    if filters.date_from is not None:
        statement = statement.where(RollCall.lesson_date >= filters.date_from)
    if filters.date_to is not None:
        statement = statement.where(RollCall.lesson_date <= filters.date_to)
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(RollCall.lesson_date.desc(), RollCall.class_id, RollCall.subject_id)
        .offset(page.offset)
        .limit(page.limit)
    )
    return [(row[0], int(row[1]), int(row[2])) for row in rows], total


async def existing_keys_on(
    session: AsyncSession, lesson_date: date, class_ids: frozenset[UUID] | None
) -> set[tuple[UUID, UUID]]:
    statement = select(RollCall.class_id, RollCall.subject_id).where(
        RollCall.lesson_date == lesson_date
    )
    if class_ids is not None:
        statement = statement.where(RollCall.class_id.in_(class_ids))
    return {(row[0], row[1]) for row in await session.execute(statement)}


# --------------------------------------------------------------------------- aggregations


def _filtered[*Ts](statement: Select[*Ts], query: AttendanceQuery) -> Select[*Ts]:
    statement = statement.where(RollCall.lesson_date.between(query.start, query.end))
    if query.class_ids is not None:
        statement = statement.where(RollCall.class_id.in_(query.class_ids))
    if query.class_id is not None:
        statement = statement.where(RollCall.class_id == query.class_id)
    if query.subject_id is not None:
        statement = statement.where(RollCall.subject_id == query.subject_id)
    return statement


def _with_student[*Ts](statement: Select[*Ts], query: AttendanceQuery) -> Select[*Ts]:
    if query.student_id is not None:
        statement = statement.where(AttendanceRecord.student_id == query.student_id)
    return statement


async def totals_by_student(
    session: AsyncSession, query: AttendanceQuery
) -> list[tuple[UUID, UUID, int, int]]:
    statement = select(AttendanceRecord.student_id, RollCall.class_id, _PRESENT, _ABSENT).join(
        RollCall, RollCall.id == AttendanceRecord.roll_call_id
    )
    statement = _with_student(_filtered(statement, query), query).group_by(
        AttendanceRecord.student_id, RollCall.class_id
    )
    return [(r[0], r[1], int(r[2]), int(r[3])) for r in await session.execute(statement)]


async def lessons(session: AsyncSession, query: AttendanceQuery) -> list[tuple[Any, ...]]:
    statement = (
        select(
            RollCall.id,
            RollCall.class_id,
            RollCall.subject_id,
            RollCall.lesson_date,
            RollCall.taken_by_id,
            RollCall.notes,
            _PRESENT,
            _ABSENT,
        )
        .outerjoin(AttendanceRecord, AttendanceRecord.roll_call_id == RollCall.id)
        .group_by(RollCall.id)
        .order_by(RollCall.lesson_date, RollCall.class_id, RollCall.subject_id)
    )
    statement = _filtered(statement, query)
    if query.student_id is not None:
        statement = statement.where(
            RollCall.id.in_(
                select(AttendanceRecord.roll_call_id).where(
                    AttendanceRecord.student_id == query.student_id
                )
            )
        )
    return [tuple(row) for row in await session.execute(statement)]


async def records(session: AsyncSession, query: AttendanceQuery) -> list[tuple[Any, ...]]:
    statement = (
        select(
            RollCall.lesson_date,
            RollCall.class_id,
            RollCall.subject_id,
            AttendanceRecord.student_id,
            AttendanceRecord.status,
        )
        .join(RollCall, RollCall.id == AttendanceRecord.roll_call_id)
        .order_by(RollCall.lesson_date, RollCall.class_id, RollCall.subject_id)
    )
    statement = _with_student(_filtered(statement, query), query)
    return [tuple(row) for row in await session.execute(statement)]


def add(session: AsyncSession, roll_call: RollCall) -> None:
    session.add(roll_call)
