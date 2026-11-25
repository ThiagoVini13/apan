from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from apan.core.dependencies import PageParamsDep, SessionDep
from apan.core.pagination import Page
from apan.modules.audit import service
from apan.modules.audit.schemas import AuditLogFilters, AuditLogRead
from apan.modules.auth.dependencies import AdminActor, get_actor

router = APIRouter(prefix="/audit-logs", tags=["audit"], dependencies=[Depends(get_actor)])


def _filters(
    action: Annotated[str | None, Query(max_length=100)] = None,
    actor_id: Annotated[UUID | None, Query(alias="actorId")] = None,
    entity_type: Annotated[str | None, Query(alias="entityType", max_length=50)] = None,
    entity_id: Annotated[str | None, Query(alias="entityId", max_length=64)] = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
) -> AuditLogFilters:
    return AuditLogFilters(
        action=action,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("", response_model=Page[AuditLogRead], operation_id="audit_logs_list")
async def list_logs(
    session: SessionDep,
    _: AdminActor,
    page: PageParamsDep,
    filters: Annotated[AuditLogFilters, Depends(_filters)],
) -> Page[AuditLogRead]:
    return await service.list_logs(session, filters, page)
