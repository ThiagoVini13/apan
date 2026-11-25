"""Password hashing, access tokens (JWT) and opaque tokens."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from apan.core.config import Settings

JWT_ALGORITHM = "HS256"
OPAQUE_TOKEN_BYTES = 32  # 256 bits

_password_hash = PasswordHash((Argon2Hasher(),))
# Verified when the e-mail does not exist, so both paths take the same time.
_DUMMY_HASH = _password_hash.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> tuple[bool, str | None]:
    """Returns (valid, new_hash). ``new_hash`` is set when the stored hash is outdated."""
    if password_hash is None:
        _password_hash.verify(password, _DUMMY_HASH)
        return False, None
    return _password_hash.verify_and_update(password, password_hash)


def burn_password_check(password: str) -> None:
    _password_hash.verify(password, _DUMMY_HASH)


def new_opaque_token() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_BYTES)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UUID
    role: str
    session_id: UUID
    expires_at: datetime


class InvalidTokenError(Exception):
    pass


def create_access_token(
    settings: Settings,
    *,
    user_id: UUID,
    role: str,
    session_id: UUID,
    now: datetime | None = None,
) -> tuple[str, int]:
    """Returns the token and its lifetime in seconds."""
    issued_at = now or datetime.now(UTC)
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "sid": str(session_id),
        "iat": issued_at,
        "exp": issued_at + ttl,
        "jti": uuid4().hex,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    token = jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm=JWT_ALGORITHM)
    return token, int(ttl.total_seconds())


def decode_access_token(settings: Settings, token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["sub", "role", "sid", "iat", "exp", "jti", "iss", "aud"]},
        )
        return AccessTokenClaims(
            user_id=UUID(payload["sub"]),
            role=str(payload["role"]),
            session_id=UUID(payload["sid"]),
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise InvalidTokenError from exc
