"""Login, sessions (refresh token rotation) and password management."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apan.core import security
from apan.core.config import Settings
from apan.core.context import Actor, ClientInfo, Role
from apan.core.errors import (
    AuthenticationError,
    BadRequestError,
    FieldError,
    ValidationError,
)
from apan.core.mail import Mailer
from apan.core.models import new_id
from apan.core.rate_limit import Rate, RateLimiter
from apan.modules.audit import service as audit
from apan.modules.auth import domain, emails, policies, repository
from apan.modules.auth.models import PasswordResetToken, RefreshToken
from apan.modules.auth.schemas import (
    LoginIn,
    MeRead,
    PasswordChangeIn,
    PasswordForgotIn,
    PasswordResetIn,
    TokenRead,
)
from apan.modules.users import User
from apan.modules.users import service as users
from apan.modules.users.schemas import UserCreate, UserRead

LOGIN_PER_IP = Rate(limit=20, window_seconds=60)
LOGIN_PER_ACCOUNT = Rate(limit=10, window_seconds=15 * 60)
REFRESH_PER_IP = Rate(limit=60, window_seconds=60)
FORGOT_PER_IP = Rate(limit=5, window_seconds=15 * 60)
FORGOT_PER_ACCOUNT = Rate(limit=3, window_seconds=60 * 60)
RESET_PER_IP = Rate(limit=10, window_seconds=15 * 60)
PASSWORD_CHANGE_PER_USER = Rate(limit=10, window_seconds=15 * 60)

USER_ENTITY = "user"


@dataclass(frozen=True, slots=True)
class IssuedSession:
    tokens: TokenRead
    refresh_token: str
    refresh_expires_at: datetime


def _now() -> datetime:
    return datetime.now(UTC)


def _account_key(email: str) -> str:
    # Keeps e-mail addresses out of Redis keys.
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _me(user: User) -> MeRead:
    role = Role(user.role)
    return MeRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=role,
        must_change_password=user.must_change_password,
        permissions=policies.permissions_for(role),
    )


def _invalid_credentials() -> AuthenticationError:
    return AuthenticationError(code="invalid_credentials")


def _invalid_session() -> AuthenticationError:
    return AuthenticationError(code="invalid_refresh_token")


def _check_password_policy(password: str, email: str, field: str = "newPassword") -> None:
    problems = domain.password_problems(password, email)
    if problems:
        raise ValidationError(
            "Password does not meet the policy.",
            code="weak_password",
            field_errors=[FieldError(field=field, code=problem) for problem in problems],
        )


def _issue(
    session: AsyncSession,
    settings: Settings,
    user: User,
    client: ClientInfo,
    now: datetime,
    *,
    family_id: UUID | None = None,
    family_expires_at: datetime | None = None,
) -> tuple[IssuedSession, RefreshToken]:
    family_id = family_id or new_id()
    family_expires_at = family_expires_at or now + timedelta(
        days=settings.refresh_token_absolute_ttl_days
    )
    plain = security.new_opaque_token()
    token = RefreshToken(
        id=new_id(),
        user_id=user.id,
        family_id=family_id,
        token_hash=security.hash_opaque_token(plain),
        expires_at=domain.refresh_expiry(now, family_expires_at, settings.refresh_token_ttl_days),
        family_expires_at=family_expires_at,
        ip=client.ip,
        user_agent=client.user_agent,
    )
    repository.add(session, token)
    access_token, expires_in = security.create_access_token(
        settings, user_id=user.id, role=user.role, session_id=family_id, now=now
    )
    issued = IssuedSession(
        tokens=TokenRead(access_token=access_token, expires_in=expires_in, user=_me(user)),
        refresh_token=plain,
        refresh_expires_at=token.expires_at,
    )
    return issued, token


# --------------------------------------------------------------------------- login / session


async def login(
    session: AsyncSession,
    limiter: RateLimiter,
    settings: Settings,
    client: ClientInfo,
    data: LoginIn,
) -> IssuedSession:
    await limiter.hit("login:ip", client.rate_limit_key, LOGIN_PER_IP)
    await limiter.hit("login:account", _account_key(data.email), LOGIN_PER_ACCOUNT)

    now = _now()
    user = await users.find_by_email(session, data.email, for_update=True)
    if user is None:
        security.burn_password_check(data.password)
        audit.record(session, "auth.login_failed", client=client, details={"reason": "unknown"})
        await session.commit()
        raise _invalid_credentials()

    if users.is_locked(user, now):
        security.burn_password_check(data.password)
        audit.record(
            session,
            "auth.login_failed",
            client=client,
            actor_id=user.id,
            details={"reason": "locked"},
        )
        await session.commit()
        raise AuthenticationError(code="account_locked")

    valid, new_hash = security.verify_password(data.password, user.password_hash)
    if not valid:
        locked = users.register_failed_login(
            user,
            now,
            max_attempts=settings.login_max_failed_attempts,
            lockout_minutes=settings.login_lockout_minutes,
        )
        audit.record(
            session,
            "auth.account_locked" if locked else "auth.login_failed",
            client=client,
            actor_id=user.id,
            details={"reason": "password", "failedCount": user.failed_login_count},
        )
        await session.commit()
        raise _invalid_credentials()

    if not user.is_active:
        audit.record(
            session,
            "auth.login_failed",
            client=client,
            actor_id=user.id,
            details={"reason": "inactive"},
        )
        await session.commit()
        raise _invalid_credentials()

    users.register_successful_login(user, now, new_hash)
    issued, token = _issue(session, settings, user, client, now)
    audit.record(
        session,
        "auth.login_succeeded",
        client=client,
        actor_id=user.id,
        details={"sessionId": str(token.family_id)},
    )
    await session.commit()
    await limiter.reset("login:account", _account_key(data.email))
    return issued


async def refresh(
    session: AsyncSession,
    limiter: RateLimiter,
    settings: Settings,
    client: ClientInfo,
    plain_token: str | None,
) -> IssuedSession:
    await limiter.hit("refresh:ip", client.rate_limit_key, REFRESH_PER_IP)
    if not plain_token:
        raise _invalid_session()

    now = _now()
    current = await repository.get_refresh_token_by_hash(
        session, security.hash_opaque_token(plain_token)
    )
    if current is None:
        raise _invalid_session()

    if current.revoked_at is not None:
        # A rotated token came back: assume theft and end the whole session.
        await repository.revoke_family(session, current.family_id, now)
        audit.record(
            session,
            "auth.refresh_token_reused",
            client=client,
            actor_id=current.user_id,
            details={"sessionId": str(current.family_id)},
        )
        await session.commit()
        raise _invalid_session()

    if current.expires_at <= now:
        raise AuthenticationError(code="refresh_token_expired")

    user = await users.find_by_id(session, current.user_id)
    if user is None or not user.is_active:
        await repository.revoke_family(session, current.family_id, now)
        await session.commit()
        raise _invalid_session()

    issued, replacement = _issue(
        session,
        settings,
        user,
        client,
        now,
        family_id=current.family_id,
        family_expires_at=current.family_expires_at,
    )
    await session.flush()
    current.revoked_at = now
    current.replaced_by_id = replacement.id
    await session.commit()
    return issued


async def logout(session: AsyncSession, client: ClientInfo, plain_token: str | None) -> None:
    if not plain_token:
        return
    current = await repository.get_refresh_token_by_hash(
        session, security.hash_opaque_token(plain_token)
    )
    if current is None:
        return
    await repository.revoke_family(session, current.family_id, _now())
    audit.record(
        session,
        "auth.logout",
        client=client,
        actor_id=current.user_id,
        details={"sessionId": str(current.family_id)},
    )
    await session.commit()


async def authenticate(session: AsyncSession, settings: Settings, access_token: str) -> Actor:
    try:
        claims = security.decode_access_token(settings, access_token)
    except security.InvalidTokenError as exc:
        raise AuthenticationError(code="invalid_token") from exc
    # Loaded on every request: deactivation and role changes apply immediately.
    user = await users.find_by_id(session, claims.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError(code="invalid_token")
    return Actor(
        user_id=user.id,
        role=Role(user.role),
        session_id=claims.session_id,
        must_change_password=user.must_change_password,
    )


async def me(session: AsyncSession, actor: Actor) -> MeRead:
    user = await users.find_by_id(session, actor.user_id)
    if user is None:
        raise AuthenticationError(code="invalid_token")
    return _me(user)


# --------------------------------------------------------------------------- passwords


async def change_password(
    session: AsyncSession,
    limiter: RateLimiter,
    actor: Actor,
    client: ClientInfo,
    data: PasswordChangeIn,
) -> None:
    await limiter.hit("password_change:user", str(actor.user_id), PASSWORD_CHANGE_PER_USER)
    user = await users.find_by_id(session, actor.user_id)
    if user is None:
        raise AuthenticationError(code="invalid_token")

    valid, _ = security.verify_password(data.current_password, user.password_hash)
    if not valid:
        raise ValidationError(
            code="invalid_current_password",
            field_errors=[FieldError(field="currentPassword", code="invalid_current_password")],
        )
    if data.new_password == data.current_password:
        raise ValidationError(
            code="weak_password",
            field_errors=[FieldError(field="newPassword", code="password_unchanged")],
        )
    _check_password_policy(data.new_password, user.email)

    now = _now()
    users.set_password(user, security.hash_password(data.new_password))
    await repository.revoke_user_tokens(session, user.id, now, keep_family_id=actor.session_id)
    audit.record(
        session,
        "auth.password_changed",
        client=client,
        actor_id=user.id,
        entity_type=USER_ENTITY,
        entity_id=user.id,
    )
    await session.commit()


def _new_reset_token(
    session: AsyncSession, user: User, purpose: domain.ResetPurpose, expires_at: datetime
) -> str:
    plain = security.new_opaque_token()
    repository.add(
        session,
        PasswordResetToken(
            user_id=user.id,
            token_hash=security.hash_opaque_token(plain),
            purpose=purpose,
            expires_at=expires_at,
        ),
    )
    return plain


async def forgot_password(
    session: AsyncSession,
    limiter: RateLimiter,
    mailer: Mailer,
    settings: Settings,
    client: ClientInfo,
    data: PasswordForgotIn,
) -> None:
    """Always succeeds from the caller's point of view (no account enumeration)."""
    await limiter.hit("forgot:ip", client.rate_limit_key, FORGOT_PER_IP)
    await limiter.hit("forgot:account", _account_key(data.email), FORGOT_PER_ACCOUNT)

    user = await users.find_by_email(session, data.email)
    if user is None or not user.is_active:
        return

    now = _now()
    await repository.invalidate_reset_tokens(session, user.id, now)
    plain = _new_reset_token(
        session,
        user,
        domain.ResetPurpose.RESET,
        now + timedelta(minutes=settings.password_reset_ttl_minutes),
    )
    audit.record(
        session,
        "auth.password_reset_requested",
        client=client,
        actor_id=user.id,
        entity_type=USER_ENTITY,
        entity_id=user.id,
    )
    await session.commit()
    mailer.send(
        emails.password_reset(
            user.email,
            user.full_name,
            settings.frontend_url,
            plain,
            settings.password_reset_ttl_minutes,
        )
    )


async def reset_password(
    session: AsyncSession,
    limiter: RateLimiter,
    client: ClientInfo,
    data: PasswordResetIn,
) -> None:
    await limiter.hit("reset:ip", client.rate_limit_key, RESET_PER_IP)
    now = _now()
    token = await repository.get_reset_token_by_hash(
        session, security.hash_opaque_token(data.token)
    )
    if token is None or token.used_at is not None or token.expires_at <= now:
        raise BadRequestError(code="invalid_reset_token")

    user = await users.find_by_id(session, token.user_id)
    if user is None or not user.is_active:
        raise BadRequestError(code="invalid_reset_token")
    _check_password_policy(data.new_password, user.email)

    users.set_password(user, security.hash_password(data.new_password))
    await repository.invalidate_reset_tokens(session, user.id, now)
    await repository.revoke_user_tokens(session, user.id, now)
    audit.record(
        session,
        "auth.password_reset",
        client=client,
        actor_id=user.id,
        entity_type=USER_ENTITY,
        entity_id=user.id,
        details={"purpose": token.purpose},
    )
    await session.commit()


# --------------------------------------------------------------------------- account creation


async def invite_user(
    session: AsyncSession,
    mailer: Mailer,
    settings: Settings,
    actor: Actor,
    client: ClientInfo,
    data: UserCreate,
) -> UserRead:
    """Creates the account without a password and e-mails a link to define one."""
    user = await users.create_account(
        session,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        password_hash=None,
        must_change_password=True,
    )
    plain = _new_reset_token(
        session,
        user,
        domain.ResetPurpose.INVITE,
        _now() + timedelta(hours=settings.invite_ttl_hours),
    )
    audit.record(
        session,
        "users.created",
        client=client,
        actor_id=actor.user_id,
        entity_type=USER_ENTITY,
        entity_id=user.id,
        details={"role": data.role},
    )
    await session.commit()
    await session.refresh(user)
    mailer.send(
        emails.invite(
            user.email, user.full_name, settings.frontend_url, plain, settings.invite_ttl_hours
        )
    )
    return users.to_read(user)


async def create_admin(
    session: AsyncSession, *, email: str, full_name: str, password: str
) -> UserRead:
    """Bootstraps an administrator from the CLI."""
    _check_password_policy(password, email, field="password")
    user = await users.create_account(
        session,
        email=email,
        full_name=full_name,
        role=Role.ADMIN,
        password_hash=security.hash_password(password),
        must_change_password=False,
    )
    audit.record(
        session,
        "users.created",
        entity_type=USER_ENTITY,
        entity_id=user.id,
        details={"role": Role.ADMIN, "via": "cli"},
    )
    await session.commit()
    await session.refresh(user)
    return users.to_read(user)
