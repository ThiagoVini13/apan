from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from apan.core.constants import API_PREFIX
from apan.core.dependencies import ClientInfoDep, PageParamsDep, SessionDep
from apan.core.pagination import ItemList, Page
from apan.modules.auth.dependencies import AdminActor, get_actor
from apan.modules.school_years import service
from apan.modules.school_years.schemas import (
    CalendarDayCreate,
    CalendarDayRead,
    SchoolYearCreate,
    SchoolYearRead,
    SchoolYearUpdate,
    TermCreate,
    TermRead,
)

router = APIRouter(prefix="/school-years", tags=["school-years"], dependencies=[Depends(get_actor)])


@router.get("", response_model=Page[SchoolYearRead], operation_id="school_years_list")
async def list_years(session: SessionDep, page: PageParamsDep) -> Page[SchoolYearRead]:
    return await service.list_years(session, page)


@router.post(
    "",
    response_model=SchoolYearRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="school_years_create",
)
async def create_year(
    body: SchoolYearCreate,
    response: Response,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> SchoolYearRead:
    year = await service.create_year(session, actor, body, client)
    response.headers["Location"] = f"{API_PREFIX}/school-years/{year.id}"
    return year


@router.get("/{year_id}", response_model=SchoolYearRead, operation_id="school_years_get")
async def get_year(year_id: UUID, session: SessionDep) -> SchoolYearRead:
    return await service.get_year(session, year_id)


@router.patch("/{year_id}", response_model=SchoolYearRead, operation_id="school_years_update")
async def update_year(
    year_id: UUID,
    body: SchoolYearUpdate,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> SchoolYearRead:
    return await service.update_year(session, actor, year_id, body, client)


@router.delete(
    "/{year_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="school_years_delete"
)
async def delete_year(
    year_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> None:
    await service.delete_year(session, actor, year_id, client)


@router.get("/{year_id}/terms", response_model=ItemList[TermRead], operation_id="terms_list")
async def list_terms(year_id: UUID, session: SessionDep) -> ItemList[TermRead]:
    return await service.list_terms(session, year_id)


@router.post(
    "/{year_id}/terms",
    response_model=TermRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="terms_create",
)
async def create_term(
    year_id: UUID,
    body: TermCreate,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> TermRead:
    return await service.create_term(session, actor, year_id, body, client)


@router.delete(
    "/{year_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="terms_delete",
)
async def delete_term(
    year_id: UUID, term_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> None:
    await service.delete_term(session, actor, year_id, term_id, client)


@router.get(
    "/{year_id}/calendar-days",
    response_model=ItemList[CalendarDayRead],
    operation_id="calendar_days_list",
)
async def list_calendar_days(year_id: UUID, session: SessionDep) -> ItemList[CalendarDayRead]:
    return await service.list_calendar_days(session, year_id)


@router.post(
    "/{year_id}/calendar-days",
    response_model=CalendarDayRead,
    status_code=status.HTTP_201_CREATED,
    operation_id="calendar_days_create",
)
async def create_calendar_day(
    year_id: UUID,
    body: CalendarDayCreate,
    session: SessionDep,
    actor: AdminActor,
    client: ClientInfoDep,
) -> CalendarDayRead:
    return await service.create_calendar_day(session, actor, year_id, body, client)


@router.delete(
    "/{year_id}/calendar-days/{day_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="calendar_days_delete",
)
async def delete_calendar_day(
    year_id: UUID, day_id: UUID, session: SessionDep, actor: AdminActor, client: ClientInfoDep
) -> None:
    await service.delete_calendar_day(session, actor, year_id, day_id, client)
