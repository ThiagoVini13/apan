from datetime import UTC, datetime, time, timedelta
from typing import Any

from sqlalchemy import Select, String, Uuid, column, func, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.pagination import PageParams
from apan.modules.audit.models import AuditLog
from apan.modules.audit.schemas import AuditLogFilters

# Lightweight reference to the users table (owned by the users module, which itself
# depends on this module) to show who acted without a circular import.
_users = table("users", column("id", Uuid), column("full_name", String))


def add(session: AsyncSession, entry: AuditLog) -> None:
    session.add(entry)


def _filtered(filters: AuditLogFilters) -> Select[Any]:
    statement: Select[Any] = select(AuditLog, _users.c.full_name).outerjoin(
        _users, _users.c.id == AuditLog.actor_id
    )
    if filters.action:
        statement = statement.where(AuditLog.action.startswith(filters.action, autoescape=True))
    if filters.actor_id is not None:
        statement = statement.where(AuditLog.actor_id == filters.actor_id)
    if filters.entity_type:
        statement = statement.where(AuditLog.entity_type == filters.entity_type)
    if filters.entity_id:
        statement = statement.where(AuditLog.entity_id == filters.entity_id)
    if filters.date_from is not None:
        statement = statement.where(
            AuditLog.created_at >= datetime.combine(filters.date_from, time.min, UTC)
        )
    if filters.date_to is not None:
        statement = statement.where(
            AuditLog.created_at
            < datetime.combine(filters.date_to + timedelta(days=1), time.min, UTC)
        )
    return statement


async def list_page(
    session: AsyncSession, filters: AuditLogFilters, page: PageParams
) -> tuple[list[tuple[AuditLog, str | None]], int]:
    statement = _filtered(filters)
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(page.offset)
        .limit(page.limit)
    )
    return [(row[0], row[1]) for row in rows], total
