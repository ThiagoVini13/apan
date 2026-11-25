from sqlalchemy.ext.asyncio import AsyncSession

from apan.modules.audit.models import AuditLog


def add(session: AsyncSession, entry: AuditLog) -> None:
    session.add(entry)
