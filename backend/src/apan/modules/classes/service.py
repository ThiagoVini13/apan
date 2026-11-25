from collections.abc import Iterable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import AccessScope, Actor, ClientInfo, Role
from apan.core.errors import ConflictError, FieldError, NotFoundError, ValidationError
from apan.core.pagination import ItemList, Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.classes import repository
from apan.modules.classes.models import SchoolClass
from apan.modules.classes.schemas import (
    ClassFilters,
    ClassInfo,
    SchoolClassCreate,
    SchoolClassRead,
    SchoolClassUpdate,
    SubjectTeacherRead,
    SubjectTeachersReplace,
)
from apan.modules.school_years import service as school_years
from apan.modules.subjects import service as subjects
from apan.modules.users import service as users

ENTITY = "school_class"
REQUIRED_FIELDS = frozenset({"name", "grade", "shift"})


def _not_found() -> NotFoundError:
    return NotFoundError(code="class_not_found")


def _read(school_class: SchoolClass, student_count: int) -> SchoolClassRead:
    return SchoolClassRead.model_validate(
        {**_columns(school_class), "student_count": student_count}
    )


def _columns(school_class: SchoolClass) -> dict[str, object]:
    return {
        "id": school_class.id,
        "school_year_id": school_class.school_year_id,
        "name": school_class.name,
        "grade": school_class.grade,
        "shift": school_class.shift,
        "room": school_class.room,
        "capacity": school_class.capacity,
        "is_active": school_class.is_active,
    }


# --------------------------------------------------------------------------- access scope


async def scope_for(session: AsyncSession, actor: Actor) -> AccessScope:
    """Admins reach every class; teachers only the classes they are assigned to."""
    if actor.role is Role.ADMIN:
        return AccessScope(class_ids=None)
    return AccessScope(class_ids=await repository.class_ids_for_teacher(session, actor.user_id))


async def require_class(session: AsyncSession, actor: Actor, class_id: UUID) -> ClassInfo:
    """The class if the actor may reach it; otherwise 404 (never reveal it exists)."""
    scope = await scope_for(session, actor)
    school_class = await repository.get(session, class_id)
    if school_class is None or not scope.allows(class_id):
        raise _not_found()
    return ClassInfo.model_validate(school_class)


async def find_class(session: AsyncSession, class_id: UUID) -> ClassInfo | None:
    school_class = await repository.get(session, class_id)
    return ClassInfo.model_validate(school_class) if school_class else None


async def find_many(session: AsyncSession, ids: Iterable[UUID]) -> dict[UUID, ClassInfo]:
    return {c.id: ClassInfo.model_validate(c) for c in await repository.get_many(session, ids)}


async def count_active_students(session: AsyncSession, class_id: UUID) -> int:
    return await repository.count_active_students(session, class_id)


# --------------------------------------------------------------------------- classes


async def list_classes(
    session: AsyncSession, actor: Actor, filters: ClassFilters, page: PageParams
) -> Page[SchoolClassRead]:
    scope = await scope_for(session, actor)
    rows, total = await repository.list_page(session, filters, scope, page)
    return Page[SchoolClassRead].build([_read(c, n) for c, n in rows], total, page)


async def get_class(session: AsyncSession, actor: Actor, class_id: UUID) -> SchoolClassRead:
    found = await repository.get_with_count(session, class_id, await scope_for(session, actor))
    if found is None:
        raise _not_found()
    return _read(*found)


async def _ensure_unique_name(
    session: AsyncSession,
    school_year_id: UUID,
    name: str,
    shift: str,
    exclude_id: UUID | None = None,
) -> None:
    if await repository.name_taken(session, school_year_id, name, shift, exclude_id=exclude_id):
        raise ConflictError(
            code="class_name_taken", field_errors=[FieldError("name", "class_name_taken")]
        )


async def create_class(
    session: AsyncSession, actor: Actor, data: SchoolClassCreate, client: ClientInfo
) -> SchoolClassRead:
    if await school_years.find_year(session, data.school_year_id) is None:
        raise ValidationError(
            code="school_year_not_found",
            field_errors=[FieldError("schoolYearId", "school_year_not_found")],
        )
    await _ensure_unique_name(session, data.school_year_id, data.name, data.shift)
    school_class = SchoolClass(
        school_year_id=data.school_year_id,
        name=data.name,
        grade=data.grade,
        shift=data.shift,
        room=data.room,
        capacity=data.capacity,
        is_active=True,
    )
    repository.add(session, school_class)
    await session.flush()
    audit.record(
        session,
        "classes.created",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=school_class.id,
    )
    await session.commit()
    return _read(school_class, 0)


async def update_class(
    session: AsyncSession, actor: Actor, class_id: UUID, data: SchoolClassUpdate, client: ClientInfo
) -> SchoolClassRead:
    school_class = await repository.get(session, class_id, for_update=True)
    if school_class is None:
        raise _not_found()

    name = data.name or school_class.name
    shift = data.shift or school_class.shift
    if (name, shift) != (school_class.name, school_class.shift):
        await _ensure_unique_name(
            session, school_class.school_year_id, name, shift, exclude_id=class_id
        )
    student_count = await repository.count_active_students(session, class_id)
    if data.capacity is not None and data.capacity < student_count:
        raise ConflictError(
            code="capacity_below_enrollments",
            field_errors=[FieldError("capacity", "capacity_below_enrollments")],
        )
    for field in data.model_fields_set:
        value = getattr(data, field)
        if value is None and field in REQUIRED_FIELDS:
            continue
        setattr(school_class, field, value)

    audit.record(
        session,
        "classes.updated",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=class_id,
        details={"fields": sorted(data.model_fields_set)},
    )
    await session.commit()
    await session.refresh(school_class)
    return _read(school_class, student_count)


async def archive_class(
    session: AsyncSession, actor: Actor, class_id: UUID, client: ClientInfo
) -> SchoolClassRead:
    school_class = await repository.get(session, class_id, for_update=True)
    if school_class is None:
        raise _not_found()
    if school_class.is_active:
        school_class.is_active = False
        audit.record(
            session,
            "classes.archived",
            client=client,
            actor_id=actor.user_id,
            entity_type=ENTITY,
            entity_id=class_id,
        )
        await session.commit()
        await session.refresh(school_class)
    return _read(school_class, await repository.count_active_students(session, class_id))


# --------------------------------------------------------------------------- subject teachers


async def list_subject_teachers(
    session: AsyncSession, actor: Actor, class_id: UUID
) -> ItemList[SubjectTeacherRead]:
    await require_class(session, actor, class_id)
    assignments = await repository.list_assignments(session, class_id)
    subject_map = await subjects.find_many(session, {a.subject_id for a in assignments})
    teacher_names = await users.full_names(session, {a.teacher_id for a in assignments})
    items = [
        SubjectTeacherRead(
            subject_id=a.subject_id,
            subject_name=subject_map[a.subject_id].name,
            subject_code=subject_map[a.subject_id].code,
            teacher_id=a.teacher_id,
            teacher_name=teacher_names.get(a.teacher_id, ""),
        )
        for a in assignments
    ]
    items.sort(key=lambda item: item.subject_name)
    return ItemList[SubjectTeacherRead].of(items)


async def replace_subject_teachers(
    session: AsyncSession,
    actor: Actor,
    class_id: UUID,
    data: SubjectTeachersReplace,
    client: ClientInfo,
) -> ItemList[SubjectTeacherRead]:
    if await repository.get(session, class_id, for_update=True) is None:
        raise _not_found()

    errors: list[FieldError] = []
    seen: set[UUID] = set()
    subject_map = await subjects.find_many(session, {i.subject_id for i in data.items})
    teachers = await users.teachers_by_id(session, {i.teacher_id for i in data.items})
    for index, item in enumerate(data.items):
        if item.subject_id in seen:
            errors.append(FieldError(f"items.{index}.subjectId", "duplicate_subject"))
        seen.add(item.subject_id)
        if item.subject_id not in subject_map:
            errors.append(FieldError(f"items.{index}.subjectId", "subject_not_found"))
        if item.teacher_id not in teachers:
            errors.append(FieldError(f"items.{index}.teacherId", "teacher_not_found"))
    if errors:
        raise ValidationError(code="invalid_subject_teachers", field_errors=errors)

    await repository.replace_assignments(
        session, class_id, [(i.subject_id, i.teacher_id) for i in data.items]
    )
    audit.record(
        session,
        "classes.subject_teachers_replaced",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=class_id,
        details={"count": len(data.items)},
    )
    await session.commit()
    return await list_subject_teachers(session, actor, class_id)


async def teacher_subject_ids(
    session: AsyncSession, class_id: UUID, teacher_id: UUID
) -> frozenset[UUID]:
    """Subjects a teacher teaches in a class (roll call authorization)."""
    return frozenset(
        a.subject_id
        for a in await repository.list_assignments(session, class_id)
        if a.teacher_id == teacher_id
    )
