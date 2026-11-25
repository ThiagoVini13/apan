from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from apan.core.constants import API_PREFIX
from apan.core.dependencies import ClientInfoDep, PageParamsDep, SessionDep
from apan.core.pagination import Page
from apan.modules.auth.dependencies import AdminActor, get_actor
from apan.modules.subjects import service
from apan.modules.subjects.schemas import SubjectCreate, SubjectRead, SubjectUpdate

router = APIRouter(prefix="/subjects", tags=["subjects"], dependencies=[Depends(get_actor)])


@router.get("", response_model=Page[SubjectRead], operation_id="subjects_list")
async def list_subjects(
    session: SessionDep,
    page: PageParamsDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> Page[SubjectRead]:
    return await service.list_subjects(session, q, page)


@router.post(
    "",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="subjects_create",
)
async def create_subject(
    body: SubjectCreate,
    response: Response,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> SubjectRead:
    subject = await service.create_subject(session, actor, body, client)
    response.headers["Location"] = f"{API_PREFIX}/subjects/{subject.id}"
    return subject


@router.get("/{subject_id}", response_model=SubjectRead, operation_id="subjects_get")
async def get_subject(subject_id: UUID, session: SessionDep) -> SubjectRead:
    return await service.get_subject(session, subject_id)


@router.patch("/{subject_id}", response_model=SubjectRead, operation_id="subjects_update")
async def update_subject(
    subject_id: UUID,
    body: SubjectUpdate,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> SubjectRead:
    return await service.update_subject(session, actor, subject_id, body, client)


@router.delete(
    "/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="subjects_delete"
)
async def delete_subject(
    subject_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> None:
    await service.delete_subject(session, actor, subject_id, client)
