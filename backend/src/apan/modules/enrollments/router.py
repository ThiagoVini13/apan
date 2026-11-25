from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from apan.core.constants import API_PREFIX
from apan.core.dependencies import ClientInfoDep, PageParamsDep, SessionDep
from apan.core.pagination import Page
from apan.modules.auth.dependencies import AdminActor, CurrentActor, get_actor
from apan.modules.enrollments import service
from apan.modules.enrollments.schemas import (
    EnrollmentCancel,
    EnrollmentCreate,
    EnrollmentFilters,
    EnrollmentRead,
    EnrollmentStatus,
    EnrollmentTransfer,
)
from apan.modules.students import service as students

router = APIRouter(prefix="/enrollments", tags=["enrollments"], dependencies=[Depends(get_actor)])


def _filters(
    student_id: Annotated[UUID | None, Query(alias="studentId")] = None,
    class_id: Annotated[UUID | None, Query(alias="classId")] = None,
    school_year_id: Annotated[UUID | None, Query(alias="schoolYearId")] = None,
    status: EnrollmentStatus | None = None,
) -> EnrollmentFilters:
    return EnrollmentFilters(
        student_id=student_id, class_id=class_id, school_year_id=school_year_id, status=status
    )


@router.get("", response_model=Page[EnrollmentRead], operation_id="enrollments_list")
async def list_enrollments(
    session: SessionDep,
    actor: CurrentActor,
    page: PageParamsDep,
    filters: Annotated[EnrollmentFilters, Depends(_filters)],
) -> Page[EnrollmentRead]:
    return await service.list_enrollments(session, actor, filters, page)


@router.post(
    "",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="enrollments_create",
)
async def create_enrollment(
    body: EnrollmentCreate,
    response: Response,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> EnrollmentRead:
    enrollment = await students.enroll_student(session, actor, body, client)
    response.headers["Location"] = f"{API_PREFIX}/enrollments/{enrollment.id}"
    return enrollment


@router.get("/{enrollment_id}", response_model=EnrollmentRead, operation_id="enrollments_get")
async def get_enrollment(
    enrollment_id: UUID, session: SessionDep, actor: CurrentActor
) -> EnrollmentRead:
    return await service.get_enrollment(session, actor, enrollment_id)


@router.post(
    "/{enrollment_id}/transfer",
    response_model=EnrollmentRead,
    operation_id="enrollments_transfer",
)
async def transfer_enrollment(
    enrollment_id: UUID,
    body: EnrollmentTransfer,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> EnrollmentRead:
    return await service.transfer(session, actor, enrollment_id, body, client)


@router.post(
    "/{enrollment_id}/cancel", response_model=EnrollmentRead, operation_id="enrollments_cancel"
)
async def cancel_enrollment(
    enrollment_id: UUID,
    body: EnrollmentCancel,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> EnrollmentRead:
    return await service.cancel(session, actor, enrollment_id, body, client)
