from datetime import date
from uuid import UUID

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.clock import local_today, now
from apan.core.context import Actor, ClientInfo
from apan.core.errors import ConflictError, FieldError, NotFoundError, ValidationError
from apan.core.pagination import ItemList, Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.classes import service as classes
from apan.modules.enrollments import service as enrollments
from apan.modules.enrollments.schemas import EnrollmentCreate, EnrollmentRead
from apan.modules.students import domain, policies, repository
from apan.modules.students.models import Guardian, Student
from apan.modules.students.schemas import (
    GuardianCreate,
    GuardianRead,
    GuardianUpdate,
    StudentCreate,
    StudentDetail,
    StudentFilters,
    StudentRead,
    StudentUpdate,
)

ENTITY = "student"


def _not_found() -> NotFoundError:
    return NotFoundError(code="student_not_found")


def _read(student: Student, current: EnrollmentRead | None) -> StudentRead:
    return StudentRead(
        id=student.id,
        enrollment_number=student.enrollment_number,
        full_name=student.full_name,
        birth_date=student.birth_date,
        archived_at=student.archived_at,
        current_class_id=current.class_id if current else None,
        current_enrollment_id=current.id if current else None,
    )


async def _with_current(session: AsyncSession, students: list[Student]) -> list[StudentRead]:
    current = await enrollments.current_by_student(session, [s.id for s in students])
    return [_read(s, current.get(s.id)) for s in students]


async def _allowed_ids(session: AsyncSession, actor: Actor) -> Select[UUID] | None:
    """Students the actor may reach (None: everyone)."""
    scope = await classes.scope_for(session, actor)
    if scope.class_ids is None:
        return None
    return enrollments.active_student_ids_query(scope.class_ids)


async def _accessible(
    session: AsyncSession, actor: Actor, student_id: UUID, *, for_update: bool = False
) -> Student:
    student = await repository.get(session, student_id, for_update=for_update)
    if student is None:
        raise _not_found()
    allowed = await _allowed_ids(session, actor)
    if allowed is not None and (
        student.archived_at is not None
        or not await repository.is_within(session, student_id, allowed)
    ):
        raise _not_found()
    return student


def _check_birth_date(birth_date: date, field: str = "birthDate") -> None:
    problem = domain.birth_date_problem(birth_date, local_today())
    if problem:
        raise ValidationError(code=problem, field_errors=[FieldError(field, problem)])


def _guardian_phone(raw: str, field: str) -> str:
    phone = domain.normalize_phone(raw)
    if phone is None:
        raise ValidationError(
            code="invalid_phone", field_errors=[FieldError(field, "invalid_phone")]
        )
    return phone


def _guardian_required() -> ConflictError:
    return ConflictError(
        code="guardian_required", field_errors=[FieldError("guardians", "guardian_required")]
    )


# --------------------------------------------------------------------------- students


async def list_students(
    session: AsyncSession, actor: Actor, filters: StudentFilters, page: PageParams
) -> Page[StudentRead]:
    allowed = await _allowed_ids(session, actor)
    if filters.class_id is not None:
        await classes.require_class(session, actor, filters.class_id)
        allowed = enrollments.active_student_ids_query([filters.class_id])
    students, total = await repository.list_page(
        session,
        q=filters.q,
        allowed=allowed,
        include_archived=filters.include_archived and policies.can_see_archived(actor),
        page=page,
    )
    return Page[StudentRead].build(await _with_current(session, students), total, page)


async def _detail(session: AsyncSession, student: Student) -> StudentDetail:
    (read,) = await _with_current(session, [student])
    guardians = await repository.list_guardians(session, student.id)
    return StudentDetail(
        **read.model_dump(), guardians=[GuardianRead.model_validate(g) for g in guardians]
    )


async def get_student(
    session: AsyncSession, actor: Actor, student_id: UUID, client: ClientInfo
) -> StudentDetail:
    student = await _accessible(session, actor, student_id)
    if actor.is_admin:
        # LGPD: an administrator opening a student's record is traceable.
        audit.record(
            session,
            "students.viewed",
            client=client,
            actor_id=actor.user_id,
            entity_type=ENTITY,
            entity_id=student.id,
        )
        await session.commit()
    return await _detail(session, student)


def _new_guardians(student_id: UUID, items: list[GuardianCreate]) -> list[Guardian]:
    if sum(1 for g in items if g.is_primary) > 1:
        raise ValidationError(
            code="multiple_primary_guardians",
            field_errors=[FieldError("guardians", "multiple_primary_guardians")],
        )
    has_primary = any(g.is_primary for g in items)
    return [
        Guardian(
            student_id=student_id,
            full_name=item.full_name,
            phone=_guardian_phone(item.phone, f"guardians.{index}.phone"),
            relationship=item.relationship,
            is_primary=item.is_primary or (not has_primary and index == 0),
        )
        for index, item in enumerate(items)
    ]


async def create_student(
    session: AsyncSession, actor: Actor, data: StudentCreate, client: ClientInfo
) -> StudentDetail:
    _check_birth_date(data.birth_date)
    if data.class_id is None and policies.requires_class_on_create(actor):
        raise ValidationError(
            code="class_required", field_errors=[FieldError("classId", "class_required")]
        )
    if domain.is_minor(data.birth_date, local_today()) and not data.guardians:
        raise ValidationError(
            code="guardian_required", field_errors=[FieldError("guardians", "guardian_required")]
        )
    if data.class_id is not None:
        # Fail early (404 for classes outside the teacher's scope) before writing anything.
        await classes.require_class(session, actor, data.class_id)

    sequence = await repository.next_enrollment_sequence(session)
    student = Student(
        enrollment_number=domain.enrollment_number(local_today().year, sequence),
        full_name=data.full_name,
        birth_date=data.birth_date,
    )
    repository.add(session, student)
    await session.flush()
    for guardian in _new_guardians(student.id, data.guardians):
        repository.add(session, guardian)
    if data.class_id is not None:
        await enrollments.add_enrollment(
            session,
            actor,
            student_id=student.id,
            class_id=data.class_id,
            starts_on=data.enrolled_on,
        )
    audit.record(
        session,
        "students.created",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=student.id,
        details={"classId": str(data.class_id) if data.class_id else None},
    )
    await session.commit()
    return await _detail(session, student)


async def update_student(
    session: AsyncSession, actor: Actor, student_id: UUID, data: StudentUpdate, client: ClientInfo
) -> StudentDetail:
    student = await _accessible(session, actor, student_id, for_update=True)
    if student.archived_at is not None:
        raise ConflictError(code="student_archived")
    if data.birth_date is not None:
        _check_birth_date(data.birth_date)
        if domain.is_minor(data.birth_date, local_today()) and not await repository.list_guardians(
            session, student.id
        ):
            raise _guardian_required()
        student.birth_date = data.birth_date
    if data.full_name is not None:
        student.full_name = data.full_name
    audit.record(
        session,
        "students.updated",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=student.id,
        details={"fields": sorted(data.model_fields_set)},
    )
    await session.commit()
    await session.refresh(student)
    return await _detail(session, student)


async def archive_student(
    session: AsyncSession, actor: Actor, student_id: UUID, client: ClientInfo
) -> StudentDetail:
    student = await _accessible(session, actor, student_id, for_update=True)
    if student.archived_at is None:
        student.archived_at = now()
        await enrollments.end_active(session, student.id, local_today())
        audit.record(
            session,
            "students.archived",
            client=client,
            actor_id=actor.user_id,
            entity_type=ENTITY,
            entity_id=student.id,
        )
        await session.commit()
        await session.refresh(student)
    return await _detail(session, student)


async def enroll_student(
    session: AsyncSession, actor: Actor, data: EnrollmentCreate, client: ClientInfo
) -> EnrollmentRead:
    student = await repository.get(session, data.student_id, for_update=True)
    if student is None:
        raise ValidationError(
            code="student_not_found", field_errors=[FieldError("studentId", "student_not_found")]
        )
    if student.archived_at is not None:
        raise ConflictError(code="student_archived")
    enrollment = await enrollments.add_enrollment(
        session, actor, student_id=student.id, class_id=data.class_id, starts_on=data.starts_on
    )
    audit.record(
        session,
        "enrollments.created",
        client=client,
        actor_id=actor.user_id,
        entity_type="enrollment",
        entity_id=enrollment.id,
    )
    await session.commit()
    return EnrollmentRead.model_validate(enrollment)


# --------------------------------------------------------------------------- guardians


async def list_guardians(
    session: AsyncSession, actor: Actor, student_id: UUID
) -> ItemList[GuardianRead]:
    await _accessible(session, actor, student_id)
    guardians = await repository.list_guardians(session, student_id)
    return ItemList[GuardianRead].of([GuardianRead.model_validate(g) for g in guardians])


async def _clear_primary(session: AsyncSession, student_id: UUID, keep: UUID | None) -> None:
    for guardian in await repository.list_guardians(session, student_id):
        if guardian.is_primary and guardian.id != keep:
            guardian.is_primary = False
    await session.flush()


async def add_guardian(
    session: AsyncSession, actor: Actor, student_id: UUID, data: GuardianCreate, client: ClientInfo
) -> GuardianRead:
    student = await _accessible(session, actor, student_id, for_update=True)
    existing = await repository.list_guardians(session, student.id)
    is_primary = data.is_primary or not existing
    if is_primary:
        await _clear_primary(session, student.id, keep=None)
    guardian = Guardian(
        student_id=student.id,
        full_name=data.full_name,
        phone=_guardian_phone(data.phone, "phone"),
        relationship=data.relationship,
        is_primary=is_primary,
    )
    repository.add(session, guardian)
    await session.flush()
    audit.record(
        session,
        "guardians.created",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=student.id,
    )
    await session.commit()
    return GuardianRead.model_validate(guardian)


async def _get_guardian(session: AsyncSession, student_id: UUID, guardian_id: UUID) -> Guardian:
    guardian = await repository.get_guardian(session, student_id, guardian_id)
    if guardian is None:
        raise NotFoundError(code="guardian_not_found")
    return guardian


async def update_guardian(
    session: AsyncSession,
    actor: Actor,
    student_id: UUID,
    guardian_id: UUID,
    data: GuardianUpdate,
    client: ClientInfo,
) -> GuardianRead:
    student = await _accessible(session, actor, student_id, for_update=True)
    guardian = await _get_guardian(session, student.id, guardian_id)
    if data.is_primary is True and not guardian.is_primary:
        await _clear_primary(session, student.id, keep=guardian.id)
        guardian.is_primary = True
    elif data.is_primary is False and guardian.is_primary:
        raise ConflictError(code="primary_guardian_required")
    if data.full_name is not None:
        guardian.full_name = data.full_name
    if data.phone is not None:
        guardian.phone = _guardian_phone(data.phone, "phone")
    if data.relationship is not None:
        guardian.relationship = data.relationship
    audit.record(
        session,
        "guardians.updated",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=student.id,
        details={"fields": sorted(data.model_fields_set)},
    )
    await session.commit()
    await session.refresh(guardian)
    return GuardianRead.model_validate(guardian)


async def delete_guardian(
    session: AsyncSession, actor: Actor, student_id: UUID, guardian_id: UUID, client: ClientInfo
) -> None:
    student = await _accessible(session, actor, student_id, for_update=True)
    guardian = await _get_guardian(session, student.id, guardian_id)
    others = [
        g for g in await repository.list_guardians(session, student.id) if g.id != guardian.id
    ]
    if not others and domain.is_minor(student.birth_date, local_today()):
        raise _guardian_required()
    await repository.delete(session, guardian)
    await session.flush()
    if guardian.is_primary and others:
        others[0].is_primary = True
    audit.record(
        session,
        "guardians.deleted",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=student.id,
    )
    await session.commit()
