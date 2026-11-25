import re
from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from apan.modules.audit.models import AuditLog
from apan.modules.auth.models import PasswordResetToken, RefreshToken
from apan.modules.auth.router import REFRESH_COOKIE
from apan.modules.users.models import User
from tests.conftest import FakeMailer
from tests.factories.users import CSRF_HEADERS, bearer, create_user, login

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"


def _token_from_mail(mailer: FakeMailer) -> str:
    match = re.search(r"#token=([\w-]+)", mailer.sent[-1].body)
    assert match, mailer.sent[-1].body
    return match.group(1)


async def _actions(session: AsyncSession) -> list[str]:
    rows = await session.execute(select(AuditLog.action).order_by(AuditLog.created_at))
    return list(rows.scalars())


# --------------------------------------------------------------------------- login


async def test_login_returns_access_token_and_refresh_cookie(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session, role=Role.ADMIN)

    response = await api.post(LOGIN, json={"email": user.email.upper(), "password": user.password})

    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["expiresIn"] == 900
    assert body["user"]["role"] == "admin"
    assert "users:manage" in body["user"]["permissions"]
    cookie = response.headers["set-cookie"]
    assert f"{REFRESH_COOKIE}=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/api/v1/auth" in cookie

    me = await api.get(ME, headers=bearer(body["accessToken"]))
    assert me.status_code == 200
    assert me.json()["email"] == user.email
    assert "auth.login_succeeded" in await _actions(db_session)


async def test_wrong_password_and_unknown_email_look_the_same(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)

    wrong = await api.post(LOGIN, json={"email": user.email, "password": "wrong-password-1"})
    unknown = await api.post(
        LOGIN, json={"email": "nobody@example.com", "password": "wrong-password-1"}
    )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["code"] == unknown.json()["code"] == "invalid_credentials"
    assert "set-cookie" not in wrong.headers


async def test_account_locks_after_repeated_failures(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)

    for _ in range(5):
        await api.post(LOGIN, json={"email": user.email, "password": "wrong-password-1"})
    locked = await api.post(LOGIN, json={"email": user.email, "password": user.password})

    assert locked.status_code == 401
    assert locked.json()["code"] == "account_locked"
    assert "auth.account_locked" in await _actions(db_session)


async def test_successful_login_resets_failure_count(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)
    for _ in range(4):
        await api.post(LOGIN, json={"email": user.email, "password": "wrong-password-1"})

    await login(api, user)

    stored = await db_session.get(User, user.id, populate_existing=True)
    assert stored is not None
    assert stored.failed_login_count == 0
    assert stored.last_login_at is not None


async def test_inactive_user_cannot_login(api: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user(db_session, active=False)

    response = await api.post(LOGIN, json={"email": user.email, "password": user.password})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_login_is_rate_limited_per_ip(api: AsyncClient) -> None:
    def payload(n: int) -> dict[str, str]:
        return {"email": f"nobody{n}@example.com", "password": "wrong-password-1"}

    statuses = [(await api.post(LOGIN, json=payload(n))).status_code for n in range(20)]
    limited = await api.post(LOGIN, json=payload(20))

    assert statuses == [401] * 20
    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limited"
    assert int(limited.headers["retry-after"]) > 0


async def test_login_is_rate_limited_per_account(api: AsyncClient) -> None:
    payload = {"email": "target@example.com", "password": "wrong-password-1"}
    statuses = [(await api.post(LOGIN, json=payload)).status_code for _ in range(11)]

    assert statuses == [401] * 10 + [429]


# --------------------------------------------------------------------------- access token


async def test_missing_or_invalid_bearer_is_rejected(api: AsyncClient) -> None:
    missing = await api.get(ME)
    invalid = await api.get(ME, headers=bearer("not-a-jwt"))

    assert missing.status_code == invalid.status_code == 401
    assert missing.json()["code"] == "not_authenticated"
    assert invalid.json()["code"] == "invalid_token"
    assert missing.headers["www-authenticate"] == "Bearer"


async def test_deactivation_applies_to_existing_tokens(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)
    token = await login(api, user)

    await db_session.execute(update(User).where(User.id == user.id).values(is_active=False))
    await db_session.commit()

    response = await api.get(ME, headers=bearer(token))
    assert response.status_code == 401


async def test_pending_password_change_only_allows_auth_endpoints(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session, role=Role.ADMIN, must_change_password=True)
    token = await login(api, user)

    me = await api.get(ME, headers=bearer(token))
    users = await api.get("/api/v1/users", headers=bearer(token))

    assert me.status_code == 200
    assert me.json()["mustChangePassword"] is True
    assert users.status_code == 403
    assert users.json()["code"] == "password_change_required"


# --------------------------------------------------------------------------- refresh / logout


async def test_refresh_rotates_the_token(api: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user(db_session)
    await login(api, user)
    first = api.cookies[REFRESH_COOKIE]

    response = await api.post(REFRESH, headers=CSRF_HEADERS)

    assert response.status_code == 200
    assert response.json()["accessToken"]
    assert api.cookies[REFRESH_COOKIE] != first


async def test_reusing_a_rotated_token_revokes_the_session(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)
    await login(api, user)
    stolen = api.cookies[REFRESH_COOKIE]
    await api.post(REFRESH, headers=CSRF_HEADERS)
    current = api.cookies[REFRESH_COOKIE]

    api.cookies.set(REFRESH_COOKIE, stolen, path="/api/v1/auth")
    reuse = await api.post(REFRESH, headers=CSRF_HEADERS)
    api.cookies.set(REFRESH_COOKIE, current, path="/api/v1/auth")
    after = await api.post(REFRESH, headers=CSRF_HEADERS)

    assert reuse.status_code == 401
    assert after.status_code == 401
    assert "auth.refresh_token_reused" in await _actions(db_session)


async def test_refresh_requires_csrf_header_and_trusted_origin(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)
    await login(api, user)

    no_header = await api.post(REFRESH, headers={"Origin": "http://test"})
    bad_origin = await api.post(
        REFRESH, headers={"X-Requested-With": "XMLHttpRequest", "Origin": "http://evil.test"}
    )
    no_origin = await api.post(REFRESH, headers={"X-Requested-With": "XMLHttpRequest"})

    for response in (no_header, bad_origin, no_origin):
        assert response.status_code == 403
        assert response.json()["code"] == "csrf_failed"


async def test_expired_refresh_token_is_rejected(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user(db_session)
    await login(api, user)
    await db_session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id)
        .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    await db_session.commit()

    response = await api.post(REFRESH, headers=CSRF_HEADERS)

    assert response.status_code == 401
    assert response.json()["code"] == "refresh_token_expired"


async def test_logout_revokes_the_session(api: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user(db_session)
    await login(api, user)
    token = api.cookies[REFRESH_COOKIE]

    response = await api.post(LOGOUT, headers=CSRF_HEADERS)
    api.cookies.set(REFRESH_COOKIE, token, path="/api/v1/auth")
    after = await api.post(REFRESH, headers=CSRF_HEADERS)

    assert response.status_code == 204
    assert f'{REFRESH_COOKIE}=""' in response.headers["set-cookie"]
    assert after.status_code == 401


# --------------------------------------------------------------------------- passwords


async def test_change_password_keeps_current_session_and_revokes_others(
    api: AsyncClient, db_session: AsyncSession, integration_app: FastAPI
) -> None:
    user = await create_user(db_session)
    other_device = AsyncClient(transport=ASGITransport(app=integration_app), base_url="http://test")
    await login(other_device, user)
    token = await login(api, user)

    response = await api.post(
        "/api/v1/auth/password/change",
        json={"currentPassword": user.password, "newPassword": "a-brand-new-passphrase"},
        headers=bearer(token),
    )

    assert response.status_code == 204
    assert (await api.post(REFRESH, headers=CSRF_HEADERS)).status_code == 200
    assert (await other_device.post(REFRESH, headers=CSRF_HEADERS)).status_code == 401
    relogin = await api.post(
        LOGIN, json={"email": user.email, "password": "a-brand-new-passphrase"}
    )
    assert relogin.status_code == 200
    await other_device.aclose()


async def test_change_password_validates_input(api: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user(db_session)
    token = await login(api, user)
    url = "/api/v1/auth/password/change"

    wrong = await api.post(
        url,
        json={"currentPassword": "not-my-password", "newPassword": "a-brand-new-passphrase"},
        headers=bearer(token),
    )
    weak = await api.post(
        url,
        json={"currentPassword": user.password, "newPassword": "1234567890"},
        headers=bearer(token),
    )

    assert wrong.status_code == 422
    assert wrong.json()["fieldErrors"] == [
        {"field": "currentPassword", "code": "invalid_current_password"}
    ]
    assert weak.status_code == 422
    assert weak.json()["fieldErrors"] == [{"field": "newPassword", "code": "password_too_common"}]


async def test_forgot_password_does_not_reveal_accounts(
    api: AsyncClient, db_session: AsyncSession, mailer: FakeMailer
) -> None:
    user = await create_user(db_session)

    unknown = await api.post("/api/v1/auth/password/forgot", json={"email": "no@example.com"})
    known = await api.post("/api/v1/auth/password/forgot", json={"email": user.email})

    assert unknown.status_code == known.status_code == 202
    assert [mail.to for mail in mailer.sent] == [user.email]
    assert "redefinir a sua senha" in mailer.sent[0].body


async def test_reset_password_flow(
    api: AsyncClient, db_session: AsyncSession, mailer: FakeMailer
) -> None:
    user = await create_user(db_session)
    await login(api, user)
    await api.post("/api/v1/auth/password/forgot", json={"email": user.email})
    token = _token_from_mail(mailer)
    new_password = "reset-passphrase-2026"

    reset = await api.post(
        "/api/v1/auth/password/reset", json={"token": token, "newPassword": new_password}
    )
    reused = await api.post(
        "/api/v1/auth/password/reset", json={"token": token, "newPassword": new_password}
    )

    assert reset.status_code == 204
    assert reused.status_code == 400
    assert reused.json()["code"] == "invalid_reset_token"
    assert (await api.post(REFRESH, headers=CSRF_HEADERS)).status_code == 401
    relogin = await api.post(LOGIN, json={"email": user.email, "password": new_password})
    assert relogin.status_code == 200


async def test_expired_reset_token_is_rejected(
    api: AsyncClient, db_session: AsyncSession, mailer: FakeMailer
) -> None:
    user = await create_user(db_session)
    await api.post("/api/v1/auth/password/forgot", json={"email": user.email})
    await db_session.execute(
        update(PasswordResetToken).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    await db_session.commit()

    response = await api.post(
        "/api/v1/auth/password/reset",
        json={"token": _token_from_mail(mailer), "newPassword": "reset-passphrase-2026"},
    )

    assert response.status_code == 400


async def test_requesting_a_new_reset_invalidates_the_previous_link(
    api: AsyncClient, db_session: AsyncSession, mailer: FakeMailer
) -> None:
    user = await create_user(db_session)
    await api.post("/api/v1/auth/password/forgot", json={"email": user.email})
    first = _token_from_mail(mailer)
    await api.post("/api/v1/auth/password/forgot", json={"email": user.email})

    response = await api.post(
        "/api/v1/auth/password/reset",
        json={"token": first, "newPassword": "reset-passphrase-2026"},
    )

    assert response.status_code == 400


# --------------------------------------------------------------------------- invite


async def test_invited_user_defines_password_through_the_link(
    api: AsyncClient, db_session: AsyncSession, mailer: FakeMailer
) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    token = await login(api, admin)

    created = await api.post(
        "/api/v1/users",
        json={
            "email": "Nova.Professora@Example.com",
            "fullName": "Nova Professora",
            "role": "teacher",
        },
        headers=bearer(token),
    )

    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "nova.professora@example.com"
    assert body["mustChangePassword"] is True
    assert created.headers["location"] == f"/api/v1/users/{body['id']}"
    assert mailer.sent[-1].to == "nova.professora@example.com"
    assert "convite" in mailer.sent[-1].subject

    cannot_login = await api.post(
        LOGIN, json={"email": "nova.professora@example.com", "password": "anything-at-all"}
    )
    assert cannot_login.status_code == 401

    reset = await api.post(
        "/api/v1/auth/password/reset",
        json={"token": _token_from_mail(mailer), "newPassword": "my-own-passphrase"},
    )
    assert reset.status_code == 204
    logged = await api.post(
        LOGIN, json={"email": "nova.professora@example.com", "password": "my-own-passphrase"}
    )
    assert logged.status_code == 200
    assert logged.json()["user"]["mustChangePassword"] is False
