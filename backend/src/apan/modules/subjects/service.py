from collections.abc import Iterable
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Actor, ClientInfo
from apan.core.database import is_foreign_key_violation
from apan.core.errors import ConflictError, FieldError, NotFoundError
from apan.core.pagination import Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.subjects import repository
from apan.modules.subjects.models import Subject
from apan.modules.subjects.schemas import SubjectCreate, SubjectRead, SubjectUpdate

ENTITY = "subject"


async def _get(session: AsyncSession, subject_id: UUID) -> Subject:
    subject = await repository.get(session, subject_id)
    if subject is None:
        raise NotFoundError(code="subject_not_found")
    return subject


async def _ensure_unique_code(
    session: AsyncSession, code: str, exclude_id: UUID | None = None
) -> None:
    if await repository.code_exists(session, code, exclude_id=exclude_id):
        raise ConflictError(
            code="subject_code_taken", field_errors=[FieldError("code", "subject_code_taken")]
        )


async def find_many(session: AsyncSession, ids: Iterable[UUID]) -> dict[UUID, SubjectRead]:
    return {s.id: SubjectRead.model_validate(s) for s in await repository.get_many(session, ids)}


async def list_subjects(
    session: AsyncSession, q: str | None, page: PageParams
) -> Page[SubjectRead]:
    subjects, total = await repository.list_page(session, q, page)
    return Page[SubjectRead].build([SubjectRead.model_validate(s) for s in subjects], total, page)


async def get_subject(session: AsyncSession, subject_id: UUID) -> SubjectRead:
    return SubjectRead.model_validate(await _get(session, subject_id))


async def create_subject(
    session: AsyncSession, actor: Actor, data: SubjectCreate, client: ClientInfo
) -> SubjectRead:
    await _ensure_unique_code(session, data.code)
    subject = Subject(name=data.name, code=data.code)
    repository.add(session, subject)
    await session.flush()
    audit.record(
        session,
        "subjects.created",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=subject.id,
    )
    await session.commit()
    return SubjectRead.model_validate(subject)


async def update_subject(
    session: AsyncSession,
    actor: Actor,
    subject_id: UUID,
    data: SubjectUpdate,
    client: ClientInfo,
) -> SubjectRead:
    subject = await _get(session, subject_id)
    if data.code is not None and data.code != subject.code:
        await _ensure_unique_code(session, data.code, exclude_id=subject.id)
        subject.code = data.code
    if data.name is not None:
        subject.name = data.name
    audit.record(
        session,
        "subjects.updated",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=subject.id,
        details={"fields": sorted(data.model_fields_set)},
    )
    await session.commit()
    await session.refresh(subject)
    return SubjectRead.model_validate(subject)


async def delete_subject(
    session: AsyncSession, actor: Actor, subject_id: UUID, client: ClientInfo
) -> None:
    subject = await _get(session, subject_id)
    await repository.delete(session, subject)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        if is_foreign_key_violation(exc):
            raise ConflictError(code="subject_in_use") from exc
        raise
    audit.record(
        session,
        "subjects.deleted",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=subject_id,
    )
    await session.commit()
