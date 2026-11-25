from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apan.modules.auth.models import PasswordResetToken, RefreshToken


async def get_refresh_token_by_hash(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def revoke_family(session: AsyncSession, family_id: UUID, now: datetime) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


async def revoke_user_tokens(
    session: AsyncSession, user_id: UUID, now: datetime, *, keep_family_id: UUID | None = None
) -> None:
    statement = update(RefreshToken).where(
        RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
    )
    if keep_family_id is not None:
        statement = statement.where(RefreshToken.family_id != keep_family_id)
    await session.execute(statement.values(revoked_at=now))


async def get_reset_token_by_hash(
    session: AsyncSession, token_hash: str
) -> PasswordResetToken | None:
    statement = (
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == token_hash)
        .with_for_update()
    )
    return (await session.execute(statement)).scalar_one_or_none()


async def invalidate_reset_tokens(session: AsyncSession, user_id: UUID, now: datetime) -> None:
    await session.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user_id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )


def add(session: AsyncSession, entity: RefreshToken | PasswordResetToken) -> None:
    session.add(entity)
