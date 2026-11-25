from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from apan.core.pagination import PageParams
from apan.modules.users.models import User
from apan.modules.users.schemas import UserFilters


async def get(session: AsyncSession, user_id: UUID, *, for_update: bool = False) -> User | None:
    statement = select(User).where(User.id == user_id)
    if for_update:
        statement = statement.with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def get_by_email(
    session: AsyncSession, email: str, *, for_update: bool = False
) -> User | None:
    statement = select(User).where(User.email == email)
    if for_update:
        statement = statement.with_for_update()
    return (await session.execute(statement)).scalar_one_or_none()


async def email_exists(
    session: AsyncSession, email: str, *, exclude_id: UUID | None = None
) -> bool:
    statement = select(User.id).where(User.email == email)
    if exclude_id is not None:
        statement = statement.where(User.id != exclude_id)
    return (await session.execute(statement.limit(1))).first() is not None


async def count_active_admins(session: AsyncSession) -> int:
    statement = select(func.count()).where(User.role == Role.ADMIN, User.is_active.is_(True))
    return (await session.execute(statement)).scalar_one()


def _filtered(filters: UserFilters) -> Select[User]:
    statement = select(User)
    if filters.q:
        pattern = f"%{filters.q.strip()}%"
        statement = statement.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    if filters.role is not None:
        statement = statement.where(User.role == filters.role)
    if filters.is_active is not None:
        statement = statement.where(User.is_active.is_(filters.is_active))
    return statement


async def list_page(
    session: AsyncSession, filters: UserFilters, page: PageParams
) -> tuple[list[User], int]:
    statement = _filtered(filters)
    total = (
        await session.execute(select(func.count()).select_from(statement.subquery()))
    ).scalar_one()
    rows = await session.execute(
        statement.order_by(User.full_name, User.id).offset(page.offset).limit(page.limit)
    )
    return list(rows.scalars()), total


def add(session: AsyncSession, user: User) -> None:
    session.add(user)
