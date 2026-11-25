from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from apan.core.constants import API_PREFIX
from apan.core.dependencies import ClientInfoDep, PageParamsDep, SessionDep
from apan.core.pagination import ItemList, Page
from apan.modules.auth.dependencies import AdminActor, CurrentActor, get_actor
from apan.modules.classes import service
from apan.modules.classes.schemas import (
    ClassFilters,
    SchoolClassCreate,
    SchoolClassRead,
    SchoolClassUpdate,
    Shift,
    SubjectTeacherRead,
    SubjectTeachersReplace,
)
from apan.modules.students import service as students
from apan.modules.students.schemas import StudentFilters, StudentRead

router = APIRouter(prefix="/classes", tags=["classes"], dependencies=[Depends(get_actor)])


def _filters(
    school_year_id: Annotated[UUID | None, Query(alias="schoolYearId")] = None,
    shift: Shift | None = None,
    is_active: Annotated[bool | None, Query(alias="isActive")] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> ClassFilters:
    return ClassFilters(school_year_id=school_year_id, shift=shift, is_active=is_active, q=q)


@router.get("", response_model=Page[SchoolClassRead], operation_id="classes_list")
async def list_classes(
    session: SessionDep,
    actor: CurrentActor,
    page: PageParamsDep,
    filters: Annotated[ClassFilters, Depends(_filters)],
) -> Page[SchoolClassRead]:
    return await service.list_classes(session, actor, filters, page)


@router.post(
    "",
    response_model=SchoolClassRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="classes_create",
)
async def create_class(
    body: SchoolClassCreate,
    response: Response,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> SchoolClassRead:
    school_class = await service.create_class(session, actor, body, client)
    response.headers["Location"] = f"{API_PREFIX}/classes/{school_class.id}"
    return school_class


@router.get("/{class_id}", response_model=SchoolClassRead, operation_id="classes_get")
async def get_class(class_id: UUID, session: SessionDep, actor: CurrentActor) -> SchoolClassRead:
    return await service.get_class(session, actor, class_id)


@router.patch("/{class_id}", response_model=SchoolClassRead, operation_id="classes_update")
async def update_class(
    class_id: UUID,
    body: SchoolClassUpdate,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> SchoolClassRead:
    return await service.update_class(session, actor, class_id, body, client)


@router.post("/{class_id}/archive", response_model=SchoolClassRead, operation_id="classes_archive")
async def archive_class(
    class_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> SchoolClassRead:
    return await service.archive_class(session, actor, class_id, client)


@router.get(
    "/{class_id}/subject-teachers",
    response_model=ItemList[SubjectTeacherRead],
    operation_id="classes_subject_teachers_list",
)
async def list_subject_teachers(
    class_id: UUID, session: SessionDep, actor: CurrentActor
) -> ItemList[SubjectTeacherRead]:
    return await service.list_subject_teachers(session, actor, class_id)


@router.put(
    "/{class_id}/subject-teachers",
    response_model=ItemList[SubjectTeacherRead],
    operation_id="classes_subject_teachers_replace",
)
async def replace_subject_teachers(
    class_id: UUID,
    body: SubjectTeachersReplace,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> ItemList[SubjectTeacherRead]:
    return await service.replace_subject_teachers(session, actor, class_id, body, client)


@router.get(
    "/{class_id}/students", response_model=Page[StudentRead], operation_id="classes_students"
)
async def list_class_students(
    class_id: UUID,
    session: SessionDep,
    actor: CurrentActor,
    page: PageParamsDep,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> Page[StudentRead]:
    return await students.list_students(
        session, actor, StudentFilters(q=q, class_id=class_id), page
    )
