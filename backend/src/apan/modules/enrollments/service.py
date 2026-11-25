"""Enrollments (matrículas).

This module does not import the students module: students orchestrate their own
enrollment, and the foreign key guarantees that the student exists.
"""

from collections.abc import Iterable
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.clock import local_today
from apan.core.context import AccessScope, Actor, ClientInfo
from apan.core.errors import ConflictError, FieldError, NotFoundError, ValidationError
from apan.core.pagination import Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.classes import service as classes
from apan.modules.classes.schemas import ClassInfo
from apan.modules.enrollments import repository
from apan.modules.enrollments.models import Enrollment
from apan.modules.enrollments.schemas import (
    EnrollmentCancel,
    EnrollmentFilters,
    EnrollmentRead,
    EnrollmentStatus,
    EnrollmentTransfer,
)
from apan.modules.school_years import service as school_years

ENTITY = "enrollment"


def _read(enrollment: Enrollment) -> EnrollmentRead:
    return EnrollmentRead.model_validate(enrollment)


def _not_found() -> NotFoundError:
    return NotFoundError(code="enrollment_not_found")


async def _check_class_can_receive(
    session: AsyncSession, school_class: ClassInfo, field: str = "classId"
) -> None:
    if not school_class.is_active:
        raise ConflictError(
            code="class_archived", field_errors=[FieldError(field, "class_archived")]
        )
    if (
        school_class.capacity is not None
        and await repository.count_active_in_class(session, school_class.id)
        >= school_class.capacity
    ):
        raise ConflictError(
            code="class_capacity_exceeded",
            field_errors=[FieldError(field, "class_capacity_exceeded")],
        )


async def _date_in_year(
    session: AsyncSession, school_year_id: UUID, on: date | None, field: str
) -> date:
    """``on`` (default: today, clipped to the year) if it falls inside the school year."""
    year = await school_years.find_year(session, school_year_id)
    if year is None:
        raise ValidationError(code="school_year_not_found")
    if on is None:
        on = min(max(local_today(), year.starts_on), year.ends_on)
    if not year.starts_on <= on <= year.ends_on:
        raise ValidationError(
            code="date_outside_school_year",
            field_errors=[FieldError(field, "date_outside_school_year")],
        )
    return on


# --------------------------------------------------------------------------- used by students


async def add_enrollment(
    session: AsyncSession,
    actor: Actor,
    *,
    student_id: UUID,
    class_id: UUID,
    starts_on: date | None,
) -> Enrollment:
    """Adds an active enrollment to the session (no commit). The caller validated the
    student; the class must be within the actor's scope."""
    school_class = await classes.require_class(session, actor, class_id)
    await _check_class_can_receive(session, school_class)
    starts_on = await _date_in_year(session, school_class.school_year_id, starts_on, "startsOn")
    if await repository.active_for_student_in_year(
        session, student_id, school_class.school_year_id
    ):
        raise ConflictError(code="student_already_enrolled")

    enrollment = Enrollment(
        student_id=student_id,
        class_id=class_id,
        school_year_id=school_class.school_year_id,
        status=EnrollmentStatus.ACTIVE,
        starts_on=starts_on,
    )
    repository.add(session, enrollment)
    await session.flush()
    return enrollment


def active_student_ids_query(class_ids: Iterable[UUID]) -> Select[UUID]:
    """Subquery of students with an active enrollment in any of ``class_ids``."""
    return repository.active_student_ids(class_ids)


async def current_by_student(
    session: AsyncSession, student_ids: Iterable[UUID]
) -> dict[UUID, EnrollmentRead]:
    """Most recent active enrollment of each student."""
    current: dict[UUID, EnrollmentRead] = {}
    for enrollment in await repository.active_for_students(session, student_ids):
        current.setdefault(enrollment.student_id, _read(enrollment))
    return current


async def end_active(session: AsyncSession, student_id: UUID, on: date) -> None:
    """Cancels the student's active enrollments (archiving). No commit."""
    for enrollment in await repository.active_for_students(session, [student_id]):
        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.ends_on = max(on, enrollment.starts_on)


# --------------------------------------------------------------------------- endpoints


async def _scope(session: AsyncSession, actor: Actor) -> AccessScope:
    return await classes.scope_for(session, actor)


async def list_enrollments(
    session: AsyncSession, actor: Actor, filters: EnrollmentFilters, page: PageParams
) -> Page[EnrollmentRead]:
    enrollments, total = await repository.list_page(
        session, filters, await _scope(session, actor), page
    )
    return Page[EnrollmentRead].build([_read(e) for e in enrollments], total, page)


async def get_enrollment(
    session: AsyncSession, actor: Actor, enrollment_id: UUID
) -> EnrollmentRead:
    enrollment = await repository.get(session, enrollment_id)
    if enrollment is None or not (await _scope(session, actor)).allows(enrollment.class_id):
        raise _not_found()
    return _read(enrollment)


async def _get_active(session: AsyncSession, enrollment_id: UUID) -> Enrollment:
    enrollment = await repository.get(session, enrollment_id, for_update=True)
    if enrollment is None:
        raise _not_found()
    if enrollment.status != EnrollmentStatus.ACTIVE:
        raise ConflictError(code="enrollment_not_active")
    return enrollment


async def transfer(
    session: AsyncSession,
    actor: Actor,
    enrollment_id: UUID,
    data: EnrollmentTransfer,
    client: ClientInfo,
) -> EnrollmentRead:
    """Moves the student to another class of the same school year."""
    current = await _get_active(session, enrollment_id)
    if data.class_id == current.class_id:
        raise ValidationError(code="same_class", field_errors=[FieldError("classId", "same_class")])
    target = await classes.find_class(session, data.class_id)
    if target is None:
        raise ValidationError(
            code="class_not_found", field_errors=[FieldError("classId", "class_not_found")]
        )
    if target.school_year_id != current.school_year_id:
        raise ValidationError(
            code="different_school_year",
            field_errors=[FieldError("classId", "different_school_year")],
        )
    await _check_class_can_receive(session, target)
    on = await _date_in_year(session, current.school_year_id, data.transfer_on, "transferOn")
    if on <= current.starts_on:
        raise ValidationError(
            code="transfer_before_start",
            field_errors=[FieldError("transferOn", "transfer_before_start")],
        )

    current.status = EnrollmentStatus.TRANSFERRED
    current.ends_on = on - timedelta(days=1)
    await session.flush()
    replacement = Enrollment(
        student_id=current.student_id,
        class_id=target.id,
        school_year_id=current.school_year_id,
        status=EnrollmentStatus.ACTIVE,
        starts_on=on,
    )
    repository.add(session, replacement)
    await session.flush()
    audit.record(
        session,
        "enrollments.transferred",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=current.id,
        details={"fromClassId": str(current.class_id), "toClassId": str(target.id)},
    )
    await session.commit()
    return _read(replacement)


async def cancel(
    session: AsyncSession,
    actor: Actor,
    enrollment_id: UUID,
    data: EnrollmentCancel,
    client: ClientInfo,
) -> EnrollmentRead:
    enrollment = await _get_active(session, enrollment_id)
    on = await _date_in_year(session, enrollment.school_year_id, data.ends_on, "endsOn")
    if on < enrollment.starts_on:
        raise ValidationError(
            code="invalid_date_range", field_errors=[FieldError("endsOn", "invalid_date_range")]
        )
    enrollment.status = EnrollmentStatus.CANCELLED
    enrollment.ends_on = on
    audit.record(
        session,
        "enrollments.cancelled",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=enrollment.id,
    )
    await session.commit()
    await session.refresh(enrollment)
    return _read(enrollment)
