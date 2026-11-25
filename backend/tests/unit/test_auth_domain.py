from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from apan.core import security
from apan.core.context import Role
from apan.modules.auth.domain import PasswordProblem, password_problems, refresh_expiry
from apan.modules.auth.policies import permissions_for
from apan.modules.users.domain import lockout_duration
from tests.conftest import make_settings

NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("password", "expected"),
    [
        ("short", [PasswordProblem.TOO_SHORT]),
        ("x" * 129 + "abcd", [PasswordProblem.TOO_LONG]),
        ("1234567890", [PasswordProblem.TOO_COMMON]),
        ("Senha123456", [PasswordProblem.TOO_COMMON]),
        ("ababababababab", [PasswordProblem.TOO_COMMON]),
        ("correct-horse-battery", []),
    ],
)
def test_password_policy(password: str, expected: list[PasswordProblem]) -> None:
    assert password_problems(password) == expected


def test_password_must_not_contain_email_local_part() -> None:
    problems = password_problems("maria.silva-2026!", "maria.silva@example.com")

    assert problems == [PasswordProblem.CONTAINS_EMAIL]


@pytest.mark.parametrize(
    ("failed", "expected_minutes"),
    [(1, None), (4, None), (5, 15), (6, None), (10, 30), (15, 60), (100, 24 * 60)],
)
def test_lockout_doubles_every_max_attempts(failed: int, expected_minutes: int | None) -> None:
    duration = lockout_duration(failed, max_attempts=5, base_minutes=15)

    assert duration == (None if expected_minutes is None else timedelta(minutes=expected_minutes))


def test_refresh_expiry_never_passes_family_limit() -> None:
    family_end = NOW + timedelta(days=3)

    assert refresh_expiry(NOW, family_end, ttl_days=7) == family_end
    assert refresh_expiry(NOW, NOW + timedelta(days=30), ttl_days=7) == NOW + timedelta(days=7)


def test_access_token_round_trip() -> None:
    settings = make_settings()
    user_id, session_id = uuid4(), uuid4()

    token, expires_in = security.create_access_token(
        settings, user_id=user_id, role=Role.TEACHER, session_id=session_id
    )
    claims = security.decode_access_token(settings, token)

    assert expires_in == 15 * 60
    assert (claims.user_id, claims.role, claims.session_id) == (user_id, "teacher", session_id)


def test_expired_access_token_is_rejected() -> None:
    settings = make_settings()
    token, _ = security.create_access_token(
        settings,
        user_id=uuid4(),
        role=Role.ADMIN,
        session_id=uuid4(),
        now=datetime.now(UTC) - timedelta(hours=1),
    )

    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(settings, token)


@pytest.mark.parametrize(
    "tamper",
    [
        {"aud": "someone-else"},
        {"iss": "someone-else"},
    ],
)
def test_token_with_wrong_claims_is_rejected(tamper: dict[str, str]) -> None:
    settings = make_settings()
    payload = {
        "sub": str(uuid4()),
        "role": "admin",
        "sid": str(uuid4()),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "jti": "x",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        **tamper,
    }
    token = jwt.encode(payload, settings.secret_key.get_secret_value(), algorithm="HS256")

    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(settings, token)


def test_unsigned_token_is_rejected() -> None:
    settings = make_settings()
    payload = {"sub": str(uuid4()), "role": "admin", "sid": str(uuid4())}
    token = jwt.encode(payload, key=None, algorithm="none")

    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(settings, token)


def test_token_signed_with_another_key_is_rejected() -> None:
    settings = make_settings()
    other = make_settings(secret_key="another-secret-key-with-more-than-32-chars")
    token, _ = security.create_access_token(
        other, user_id=uuid4(), role=Role.ADMIN, session_id=uuid4()
    )

    with pytest.raises(security.InvalidTokenError):
        security.decode_access_token(settings, token)


def test_outdated_password_hash_is_upgraded() -> None:
    from pwdlib import PasswordHash
    from pwdlib.hashers.argon2 import Argon2Hasher

    weak = PasswordHash((Argon2Hasher(time_cost=1, memory_cost=8 * 1024),))
    stored = weak.hash("correct-horse-battery")

    valid, new_hash = security.verify_password("correct-horse-battery", stored)

    assert valid is True
    assert new_hash is not None and new_hash != stored


def test_teacher_permissions_are_a_subset_of_scoped_actions() -> None:
    assert "users:manage" not in permissions_for(Role.TEACHER)
    assert "users:manage" in permissions_for(Role.ADMIN)
