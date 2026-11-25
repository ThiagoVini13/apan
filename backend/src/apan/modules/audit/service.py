"""Audit trail. Entries join the caller's transaction; the caller commits."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import ClientInfo
from apan.core.pagination import Page, PageParams
from apan.modules.audit import repository
from apan.modules.audit.models import AuditLog
from apan.modules.audit.schemas import AuditLogFilters, AuditLogRead


def record(
    session: AsyncSession,
    action: str,
    *,
    client: ClientInfo | None = None,
    actor_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    repository.add(
        session,
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details or {},
            ip=client.ip if client else None,
            user_agent=client.user_agent if client else None,
        ),
    )


async def list_logs(
    session: AsyncSession, filters: AuditLogFilters, page: PageParams
) -> Page[AuditLogRead]:
    rows, total = await repository.list_page(session, filters, page)
    items = [
        AuditLogRead(
            id=entry.id,
            actor_id=entry.actor_id,
            actor_name=actor_name,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            details=entry.details,
            ip=entry.ip,
            created_at=entry.created_at,
        )
        for entry, actor_name in rows
    ]
    return Page[AuditLogRead].build(items, total, page)
