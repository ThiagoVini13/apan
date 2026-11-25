from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Actor, ClientInfo, Role
from apan.core.errors import ConflictError, FieldError, NotFoundError, PermissionDeniedError
from apan.core.pagination import Page, PageParams
from apan.modules.audit import service as audit
from apan.modules.users import domain, policies, repository
from apan.modules.users.models import User
from apan.modules.users.schemas import UserFilters, UserRead, UserUpdate

ENTITY = "user"


def to_read(user: User) -> UserRead:
    return UserRead.model_validate(user)


def _not_found() -> NotFoundError:
    return NotFoundError(code="user_not_found")


def _email_taken() -> ConflictError:
    return ConflictError(
        code="email_taken", field_errors=[FieldError(field="email", code="email_taken")]
    )


# --------------------------------------------------------------------------- queries


async def list_users(
    session: AsyncSession, filters: UserFilters, page: PageParams
) -> Page[UserRead]:
    users, total = await repository.list_page(session, filters, page)
    return Page[UserRead].build([to_read(u) for u in users], total, page)


async def get_user(session: AsyncSession, actor: Actor, user_id: UUID) -> UserRead:
    if not policies.can_read(actor, user_id):
        raise _not_found()
    user = await repository.get(session, user_id)
    if user is None:
        raise _not_found()
    return to_read(user)


async def find_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await repository.get(session, user_id)


async def find_by_email(
    session: AsyncSession, email: str, *, for_update: bool = False
) -> User | None:
    return await repository.get_by_email(
        session, domain.normalize_email(email), for_update=for_update
    )


# --------------------------------------------------------------------------- commands


async def create_account(
    session: AsyncSession,
    *,
    email: str,
    full_name: str,
    role: Role,
    password_hash: str | None,
    must_change_password: bool,
) -> User:
    """Adds the user to the session (no commit): the caller owns the transaction."""
    email = domain.normalize_email(email)
    if await repository.email_exists(session, email):
        raise _email_taken()
    user = User(
        email=email,
        full_name=full_name,
        role=role,
        password_hash=password_hash,
        must_change_password=must_change_password,
        is_active=True,
        failed_login_count=0,
    )
    repository.add(session, user)
    await session.flush()
    return user


async def _ensure_not_last_admin(session: AsyncSession, user: User) -> None:
    if (
        user.role == Role.ADMIN
        and user.is_active
        and await repository.count_active_admins(session) <= 1
    ):
        raise ConflictError(code="last_admin")


async def update_user(
    session: AsyncSession,
    actor: Actor,
    user_id: UUID,
    changes: UserUpdate,
    client: ClientInfo,
) -> UserRead:
    if not policies.can_read(actor, user_id):
        raise _not_found()
    if not policies.can_update(actor, user_id, changes):
        raise PermissionDeniedError(code="permission_denied")
    user = await repository.get(session, user_id, for_update=True)
    if user is None:
        raise _not_found()

    changed: list[str] = []
    if changes.email is not None:
        email = domain.normalize_email(changes.email)
        if email != user.email:
            if await repository.email_exists(session, email, exclude_id=user.id):
                raise _email_taken()
            user.email = email
            changed.append("email")
    if changes.full_name is not None and changes.full_name != user.full_name:
        user.full_name = changes.full_name
        changed.append("fullName")
    if changes.role is not None and changes.role != user.role:
        if changes.role != Role.ADMIN:
            await _ensure_not_last_admin(session, user)
        user.role = changes.role
        changed.append("role")

    if changed:
        audit.record(
            session,
            "users.updated",
            client=client,
            actor_id=actor.user_id,
            entity_type=ENTITY,
            entity_id=user.id,
            details={"fields": changed},
        )
        await session.commit()
        await session.refresh(user)
    return to_read(user)


async def set_active(
    session: AsyncSession, actor: Actor, user_id: UUID, *, active: bool, client: ClientInfo
) -> UserRead:
    user = await repository.get(session, user_id, for_update=True)
    if user is None:
        raise _not_found()
    if user.is_active == active:
        return to_read(user)
    if not active:
        if user.id == actor.user_id:
            raise ConflictError(code="cannot_deactivate_self")
        await _ensure_not_last_admin(session, user)

    user.is_active = active
    audit.record(
        session,
        "users.activated" if active else "users.deactivated",
        client=client,
        actor_id=actor.user_id,
        entity_type=ENTITY,
        entity_id=user.id,
    )
    await session.commit()
    await session.refresh(user)
    return to_read(user)


# --------------------------------------------------------------------------- login bookkeeping
# These mutate the loaded user; the auth service commits.


def register_failed_login(
    user: User, now: datetime, *, max_attempts: int, lockout_minutes: int
) -> bool:
    """Counts a failure and returns True when the account just got locked."""
    user.failed_login_count += 1
    duration = domain.lockout_duration(user.failed_login_count, max_attempts, lockout_minutes)
    if duration is None:
        return False
    user.locked_until = now + duration
    return True


def register_successful_login(user: User, now: datetime, new_password_hash: str | None) -> None:
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    if new_password_hash is not None:
        user.password_hash = new_password_hash


def set_password(user: User, password_hash: str) -> None:
    user.password_hash = password_hash
    user.must_change_password = False
    user.failed_login_count = 0
    user.locked_until = None


def is_locked(user: User, now: datetime) -> bool:
    return domain.is_locked(user.locked_until, now)
