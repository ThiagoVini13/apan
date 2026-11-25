"""Audit trail. Entries join the caller's transaction; the caller commits."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import ClientInfo
from apan.modules.audit import repository
from apan.modules.audit.models import AuditLog


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
