from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from apan.core.dependencies import ClientInfoDep, PageParamsDep, SessionDep, SettingsDep
from apan.core.pagination import Page
from apan.modules.auth.dependencies import CurrentActor, get_actor
from apan.modules.roll_calls import service
from apan.modules.roll_calls.schemas import (
    RollCallFilters,
    RollCallRead,
    RollCallSheet,
    RollCallSummary,
    RollCallUpsert,
)

router = APIRouter(prefix="/roll-calls", tags=["roll-calls"], dependencies=[Depends(get_actor)])


def _filters(
    class_id: Annotated[UUID | None, Query(alias="classId")] = None,
    subject_id: Annotated[UUID | None, Query(alias="subjectId")] = None,
    lesson_date: Annotated[date | None, Query(alias="date")] = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
) -> RollCallFilters:
    return RollCallFilters(
        class_id=class_id,
        subject_id=subject_id,
        lesson_date=lesson_date,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("", response_model=Page[RollCallSummary], operation_id="roll_calls_list")
async def list_roll_calls(
    session: SessionDep,
    actor: CurrentActor,
    page: PageParamsDep,
    filters: Annotated[RollCallFilters, Depends(_filters)],
) -> Page[RollCallSummary]:
    return await service.list_roll_calls(session, actor, filters, page)


@router.get("/sheet", response_model=RollCallSheet, operation_id="roll_calls_sheet")
async def get_sheet(
    session: SessionDep,
    settings: SettingsDep,
    actor: CurrentActor,
    class_id: Annotated[UUID, Query(alias="classId")],
    subject_id: Annotated[UUID, Query(alias="subjectId")],
    lesson_date: Annotated[date, Query(alias="date")],
) -> RollCallSheet:
    """Roster of a lesson with any marks already saved, and whether it can be edited."""
    return await service.get_sheet(session, settings, actor, class_id, subject_id, lesson_date)


@router.put("", response_model=RollCallRead, operation_id="roll_calls_upsert")
async def upsert_roll_call(
    body: RollCallUpsert,
    session: SessionDep,
    settings: SettingsDep,
    actor: CurrentActor,
    client: ClientInfoDep,
) -> RollCallRead:
    """Creates or replaces the roll call of (classId, subjectId, lessonDate). Safe to retry."""
    return await service.upsert(session, settings, actor, body, client)


@router.get("/{roll_call_id}", response_model=RollCallRead, operation_id="roll_calls_get")
async def get_roll_call(
    roll_call_id: UUID, session: SessionDep, actor: CurrentActor
) -> RollCallRead:
    return await service.get_roll_call(session, actor, roll_call_id)
