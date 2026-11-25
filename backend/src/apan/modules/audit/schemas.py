from datetime import date, datetime
from typing import Any
from uuid import UUID

from apan.core.schemas import ApiModel


class AuditLogRead(ApiModel):
    id: UUID
    actor_id: UUID | None
    actor_name: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: dict[str, Any]
    ip: str | None
    created_at: datetime


class AuditLogFilters(ApiModel):
    action: str | None = None
    actor_id: UUID | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
