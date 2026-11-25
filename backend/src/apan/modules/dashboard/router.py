from fastapi import APIRouter, Depends

from apan.core.dependencies import SessionDep
from apan.modules.auth.dependencies import CurrentActor, get_actor
from apan.modules.dashboard import service
from apan.modules.dashboard.schemas import DashboardToday

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_actor)])


@router.get("/today", response_model=DashboardToday, operation_id="dashboard_today")
async def today(session: SessionDep, actor: CurrentActor) -> DashboardToday:
    return await service.today(session, actor)
