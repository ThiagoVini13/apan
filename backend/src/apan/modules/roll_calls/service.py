"""Roll calls: one per class, subject and lesson date (idempotent upsert)."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core import clock
from apan.core.config import Settings
from apan.core.context import Actor, ClientInfo
from apan.core.errors import (
    ConflictError,
    FieldError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from apan.core.pagination import Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.classes import service as classes
from apan.modules.classes.schemas import ClassInfo
from apan.modules.enrollments import service as enrollments
from apan.modules.roll_calls import domain, repository
from apan.modules.roll_calls.models import RollCall
from apan.modules.roll_calls.schemas import (
    AttendanceQuery,
    AttendanceRead,
    AttendanceStatus,
    LessonRow,
    RecordRow,
    RollCallFilters,
    RollCallRead,
    RollCallSheet,
    RollCallSummary,
    RollCallUpsert,
    SheetStudent,
    StudentTotals,
)
from apan.modules.school_years import service as school_years
from apan.modules.students import service as students
from apan.modules.subjects import service as subjects

ENTITY = "roll_call"


@dataclass(frozen=True, slots=True)
class _Lesson:
    school_class: ClassInfo
    is_school_day: bool
    within_window: bool


def _field(code: str, field: str) -> list[FieldError]:
    return [FieldError(field, code)]


async def _lesson(
    session: AsyncSession,
    settings: Settings,
    actor: Actor,
    class_id: UUID,
    subject_id: UUID,
    lesson_date: date,
) -> _Lesson:
    """Checks everything that does not depend on the edit window or the calendar."""
    school_class = await classes.require_class(session, actor, class_id)
    if subject_id not in await subjects.find_many(session, [subject_id]):
        raise ValidationError(
            code="subject_not_found", field_errors=_field("subject_not_found", "subjectId")
        )
    if not actor.is_admin and subject_id not in await classes.teacher_subject_ids(
        session, class_id, actor.user_id
    ):
        raise PermissionDeniedError(code="subject_not_assigned")

    today = clock.local_today()
    if lesson_date > today:
        raise ValidationError(
            code="lesson_in_future", field_errors=_field("lesson_in_future", "lessonDate")
        )
    year = await school_years.find_year(session, school_class.school_year_id)
    if year is None or not year.starts_on <= lesson_date <= year.ends_on:
        raise ValidationError(
            code="date_outside_school_year",
            field_errors=_field("date_outside_school_year", "lessonDate"),
        )
    school_day = lesson_date in await school_years.school_days(
        session, school_class.school_year_id, lesson_date, lesson_date
    )
    return _Lesson(
        school_class=school_class,
        is_school_day=school_day,
        within_window=actor.is_admin
        or domain.within_edit_window(lesson_date, today, settings.roll_call_edit_window_days),
    )


async def _read(session: AsyncSession, roll_call: RollCall) -> RollCallRead:
    records = await repository.records_for(session, roll_call.id)
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    return RollCallRead(
        id=roll_call.id,
        class_id=roll_call.class_id,
        subject_id=roll_call.subject_id,
        lesson_date=roll_call.lesson_date,
        notes=roll_call.notes,
        taken_by_id=roll_call.taken_by_id,
        updated_by_id=roll_call.updated_by_id,
        created_at=roll_call.created_at,
        updated_at=roll_call.updated_at,
        present_count=present,
        absent_count=len(records) - present,
        attendances=[
            AttendanceRead(student_id=r.student_id, status=AttendanceStatus(r.status))
            for r in sorted(records, key=lambda r: str(r.student_id))
        ],
    )


# --------------------------------------------------------------------------- endpoints


async def get_sheet(
    session: AsyncSession,
    settings: Settings,
    actor: Actor,
    class_id: UUID,
    subject_id: UUID,
    lesson_date: date,
) -> RollCallSheet:
    lesson = await _lesson(session, settings, actor, class_id, subject_id, lesson_date)
    roster = await enrollments.student_ids_on(session, class_id, lesson_date)
    people = await students.find_many(session, roster)
    existing = await repository.get_by_key(session, class_id, subject_id, lesson_date)
    marks = (
        {
            r.student_id: AttendanceStatus(r.status)
            for r in await repository.records_for(session, existing.id)
        }
        if existing
        else {}
    )
    sheet_students = sorted(
        (
            SheetStudent(
                student_id=student_id,
                full_name=people[student_id].full_name,
                enrollment_number=people[student_id].enrollment_number,
                status=marks.get(student_id),
            )
            for student_id in roster
            if student_id in people
        ),
        key=lambda s: (s.full_name.casefold(), s.enrollment_number),
    )
    return RollCallSheet(
        class_id=class_id,
        subject_id=subject_id,
        lesson_date=lesson_date,
        roll_call_id=existing.id if existing else None,
        notes=existing.notes if existing else None,
        is_school_day=lesson.is_school_day,
        editable=lesson.is_school_day and lesson.within_window and lesson.school_class.is_active,
        students=sheet_students,
    )


async def upsert(
    session: AsyncSession,
    settings: Settings,
    actor: Actor,
    data: RollCallUpsert,
    client: ClientInfo,
) -> RollCallRead:
    lesson = await _lesson(
        session, settings, actor, data.class_id, data.subject_id, data.lesson_date
    )
    if not lesson.school_class.is_active:
        raise ConflictError(code="class_archived")
    if not lesson.is_school_day:
        raise ValidationError(
            code="not_a_school_day", field_errors=_field("not_a_school_day", "lessonDate")
        )
    if not lesson.within_window:
        raise ConflictError(code="roll_call_locked")

    submitted = [a.student_id for a in data.attendances]
    if len(set(submitted)) != len(submitted):
        raise ValidationError(
            code="duplicate_student", field_errors=_field("duplicate_student", "attendances")
        )
    roster = set(await enrollments.student_ids_on(session, data.class_id, data.lesson_date))
    if extra := set(submitted) - roster:
        raise ValidationError(
            f"Not enrolled on the lesson date: {sorted(map(str, extra))}",
            code="student_not_enrolled",
            field_errors=_field("student_not_enrolled", "attendances"),
        )
    if missing := roster - set(submitted):
        raise ValidationError(
            f"Missing students: {sorted(map(str, missing))}",
            code="roll_call_incomplete",
            field_errors=_field("roll_call_incomplete", "attendances"),
        )

    roll_call = await repository.get_by_key(
        session, data.class_id, data.subject_id, data.lesson_date, for_update=True
    )
    created = roll_call is None
    if roll_call is None:
        roll_call = RollCall(
            class_id=data.class_id,
            subject_id=data.subject_id,
            lesson_date=data.lesson_date,
            taken_by_id=actor.user_id,
            updated_by_id=actor.user_id,
            notes=data.notes or None,
        )
        repository.add(session, roll_call)
        await session.flush()
    else:
        roll_call.notes = data.notes or None
        roll_call.updated_by_id = actor.user_id
    await repository.replace_records(
        session, roll_call.id, [(a.student_id, a.status.value) for a in data.attendances]
    )
    audit.record(
        session,
        "roll_calls.created" if created else "roll_calls.updated",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=roll_call.id,
        details={"students": len(data.attendances)},
    )
    await session.commit()
    await session.refresh(roll_call)
    return await _read(session, roll_call)


async def get_roll_call(session: AsyncSession, actor: Actor, roll_call_id: UUID) -> RollCallRead:
    roll_call = await repository.get(session, roll_call_id)
    scope = await classes.scope_for(session, actor)
    if roll_call is None or not scope.allows(roll_call.class_id):
        raise NotFoundError(code="roll_call_not_found")
    return await _read(session, roll_call)


async def list_roll_calls(
    session: AsyncSession, actor: Actor, filters: RollCallFilters, page: PageParams
) -> Page[RollCallSummary]:
    if filters.class_id is not None:
        await classes.require_class(session, actor, filters.class_id)
    rows, total = await repository.list_page(
        session, filters, await classes.scope_for(session, actor), page
    )
    items = [
        RollCallSummary(
            id=rc.id,
            class_id=rc.class_id,
            subject_id=rc.subject_id,
            lesson_date=rc.lesson_date,
            notes=rc.notes,
            present_count=present,
            absent_count=absent,
        )
        for rc, present, absent in rows
    ]
    return Page[RollCallSummary].build(items, total, page)


# --------------------------------------------------------------------------- aggregations
# Callers (reports, dashboard) are responsible for scoping ``query.class_ids``.


async def totals_by_student(session: AsyncSession, query: AttendanceQuery) -> list[StudentTotals]:
    return [
        StudentTotals(student_id=s, class_id=c, present=p, absent=a)
        for s, c, p, a in await repository.totals_by_student(session, query)
    ]


async def lessons(session: AsyncSession, query: AttendanceQuery) -> list[LessonRow]:
    return [
        LessonRow(
            roll_call_id=row[0],
            class_id=row[1],
            subject_id=row[2],
            lesson_date=row[3],
            taken_by_id=row[4],
            notes=row[5],
            present=int(row[6]),
            absent=int(row[7]),
        )
        for row in await repository.lessons(session, query)
    ]


async def records(session: AsyncSession, query: AttendanceQuery) -> list[RecordRow]:
    return [
        RecordRow(
            lesson_date=row[0],
            class_id=row[1],
            subject_id=row[2],
            student_id=row[3],
            status=AttendanceStatus(row[4]),
        )
        for row in await repository.records(session, query)
    ]


async def taken_on(
    session: AsyncSession, lesson_date: date, class_ids: frozenset[UUID] | None
) -> set[tuple[UUID, UUID]]:
    """(class_id, subject_id) pairs that already have a roll call on ``lesson_date``."""
    return await repository.existing_keys_on(session, lesson_date, class_ids)
