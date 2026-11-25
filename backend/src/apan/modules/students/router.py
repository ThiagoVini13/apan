from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from apan.core.constants import API_PREFIX
from apan.core.dependencies import ClientInfoDep, PageParamsDep, SessionDep
from apan.core.pagination import ItemList, Page
from apan.modules.auth.dependencies import AdminActor, CurrentActor, get_actor
from apan.modules.students import service
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

router = APIRouter(prefix="/students", tags=["students"], dependencies=[Depends(get_actor)])


def _filters(
    q: Annotated[str | None, Query(max_length=100)] = None,
    class_id: Annotated[UUID | None, Query(alias="classId")] = None,
    include_archived: Annotated[bool, Query(alias="includeArchived")] = False,
) -> StudentFilters:
    return StudentFilters(q=q, class_id=class_id, include_archived=include_archived)


@router.get("", response_model=Page[StudentRead], operation_id="students_list")
async def list_students(
    session: SessionDep,
    actor: CurrentActor,
    page: PageParamsDep,
    filters: Annotated[StudentFilters, Depends(_filters)],
) -> Page[StudentRead]:
    return await service.list_students(session, actor, filters, page)


@router.post(
    "",
    response_model=StudentDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="students_create",
)
async def create_student(
    body: StudentCreate,
    response: Response,
    session: SessionDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> StudentDetail:
    student = await service.create_student(session, actor, body, client)
    response.headers["Location"] = f"{API_PREFIX}/students/{student.id}"
    return student


@router.get("/{student_id}", response_model=StudentDetail, operation_id="students_get")
async def get_student(
    student_id: UUID, session: SessionDep, actor: CurrentActor, client: ClientInfoDep
) -> StudentDetail:
    return await service.get_student(session, actor, student_id, client)


@router.patch("/{student_id}", response_model=StudentDetail, operation_id="students_update")
async def update_student(
    student_id: UUID,
    body: StudentUpdate,
    session: SessionDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> StudentDetail:
    return await service.update_student(session, actor, student_id, body, client)


@router.post("/{student_id}/archive", response_model=StudentDetail, operation_id="students_archive")
async def archive_student(
    student_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> StudentDetail:
    return await service.archive_student(session, actor, student_id, client)


@router.get(
    "/{student_id}/guardians",
    response_model=ItemList[GuardianRead],
    operation_id="guardians_list",
)
async def list_guardians(
    student_id: UUID, session: SessionDep, actor: CurrentActor
) -> ItemList[GuardianRead]:
    return await service.list_guardians(session, actor, student_id)


@router.post(
    "/{student_id}/guardians",
    response_model=GuardianRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="guardians_create",
)
async def add_guardian(
    student_id: UUID,
    body: GuardianCreate,
    session: SessionDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> GuardianRead:
    return await service.add_guardian(session, actor, student_id, body, client)


@router.patch(
    "/{student_id}/guardians/{guardian_id}",
    response_model=GuardianRead,
    operation_id="guardians_update",
)
async def update_guardian(
    student_id: UUID,
    guardian_id: UUID,
    body: GuardianUpdate,
    session: SessionDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> GuardianRead:
    return await service.update_guardian(session, actor, student_id, guardian_id, body, client)


@router.delete(
    "/{student_id}/guardians/{guardian_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="guardians_delete",
)
async def delete_guardian(
    student_id: UUID,
    guardian_id: UUID,
    session: SessionDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> None:
    await service.delete_guardian(session, actor, student_id, guardian_id, client)
