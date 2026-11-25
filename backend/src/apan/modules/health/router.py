from fastapi import APIRouter, Response, status

from apan.core.dependencies import DatabaseDep, RedisDep
from apan.modules.health import service
from apan.modules.health.schemas import HealthRead, HealthStatus

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthRead, operation_id="health_live")
async def live() -> HealthRead:
    return HealthRead(status=HealthStatus.OK)


@router.get(
    "/ready",
    response_model=HealthRead,
    operation_id="health_ready",
    responses={503: {"model": HealthRead}},
)
async def ready(database: DatabaseDep, redis: RedisDep, response: Response) -> HealthRead:
    if await service.is_ready(database, redis):
        return HealthRead(status=HealthStatus.OK)
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthRead(status=HealthStatus.UNAVAILABLE)
