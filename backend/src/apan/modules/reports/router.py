from collections.abc import Iterator
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from apan.core.dependencies import ClientInfoDep, SessionDep
from apan.core.pagination import ItemList
from apan.modules.auth.dependencies import CurrentActor, get_actor
from apan.modules.reports import service
from apan.modules.reports.schemas import (
    AttendanceSummary,
    ClassReportRow,
    ExportFormat,
    ReportParams,
    StudentReportRow,
)

router = APIRouter(
    prefix="/reports/attendance", tags=["reports"], dependencies=[Depends(get_actor)]
)

CHUNK_SIZE = 64 * 1024


def _params(
    date_from: Annotated[date, Query(alias="from")],
    date_to: Annotated[date, Query(alias="to")],
    class_id: Annotated[UUID | None, Query(alias="classId")] = None,
    subject_id: Annotated[UUID | None, Query(alias="subjectId")] = None,
    student_id: Annotated[UUID | None, Query(alias="studentId")] = None,
) -> ReportParams:
    return ReportParams(
        date_from=date_from,
        date_to=date_to,
        class_id=class_id,
        subject_id=subject_id,
        student_id=student_id,
    )


Params = Annotated[ReportParams, Depends(_params)]


@router.get("/summary", response_model=AttendanceSummary, operation_id="reports_summary")
async def summary(session: SessionDep, actor: CurrentActor, params: Params) -> AttendanceSummary:
    return await service.summary(session, actor, params)


@router.get(
    "/students", response_model=ItemList[StudentReportRow], operation_id="reports_by_student"
)
async def by_student(
    session: SessionDep, actor: CurrentActor, params: Params
) -> ItemList[StudentReportRow]:
    return await service.by_student(session, actor, params)


@router.get("/by-class", response_model=ItemList[ClassReportRow], operation_id="reports_by_class")
async def by_class(
    session: SessionDep, actor: CurrentActor, params: Params
) -> ItemList[ClassReportRow]:
    return await service.by_class(session, actor, params)


@router.get(
    "/low-attendance",
    response_model=ItemList[StudentReportRow],
    operation_id="reports_low_attendance",
)
async def low_attendance(
    session: SessionDep, actor: CurrentActor, params: Params
) -> ItemList[StudentReportRow]:
    return await service.low_attendance(session, actor, params)


@router.get(
    "/export",
    operation_id="reports_export",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {media: {} for media in service.MEDIA_TYPES.values()},
            "description": "Spreadsheet file",
        }
    },
)
async def export_report(
    session: SessionDep,
    actor: CurrentActor,
    params: Params,
    client: ClientInfoDep,
    fmt: Annotated[ExportFormat, Query(alias="format")] = ExportFormat.XLSX,
) -> StreamingResponse:
    file = await service.export_report(session, actor, params, fmt, client)

    def chunks() -> Iterator[bytes]:
        for start in range(0, len(file.content), CHUNK_SIZE):
            yield file.content[start : start + CHUNK_SIZE]

    return StreamingResponse(
        chunks(),
        media_type=file.media_type,
        headers={
            # The filename is built from validated dates only, so it is safe as is.
            "Content-Disposition": f'attachment; filename="{file.filename}"',
            "Cache-Control": "no-store",
        },
    )
