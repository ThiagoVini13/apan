from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from apan.core.config import Settings
from apan.core.constants import API_PREFIX
from apan.core.dependencies import (
    ClientInfoDep,
    MailerDep,
    RateLimiterDep,
    SessionDep,
    SettingsDep,
)
from apan.modules.auth import service
from apan.modules.auth.dependencies import PendingPasswordActor, verify_csrf
from apan.modules.auth.schemas import (
    LoginIn,
    MeRead,
    PasswordChangeIn,
    PasswordForgotIn,
    PasswordResetIn,
    TokenRead,
)

REFRESH_COOKIE = "apan_refresh"
REFRESH_COOKIE_PATH = f"{API_PREFIX}/auth"

router = APIRouter(prefix="/auth", tags=["auth"])

RefreshCookie = Annotated[str | None, Cookie(alias=REFRESH_COOKIE)]


def _set_refresh_cookie(
    response: Response, settings: Settings, token: str, expires_at: datetime
) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=max(int((expires_at - datetime.now(UTC)).total_seconds()), 0),
        path=REFRESH_COOKIE_PATH,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="strict",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        REFRESH_COOKIE,
        path=REFRESH_COOKIE_PATH,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite="strict",
    )


@router.post("/login", response_model=TokenRead, operation_id="auth_login")
async def login(
    body: LoginIn,
    response: Response,
    session: SessionDep,
    limiter: RateLimiterDep,
    settings: SettingsDep,
    client: ClientInfoDep,
) -> TokenRead:
    issued = await service.login(session, limiter, settings, client, body)
    _set_refresh_cookie(response, settings, issued.refresh_token, issued.refresh_expires_at)
    return issued.tokens


@router.post(
    "/refresh",
    response_model=TokenRead,
    operation_id="auth_refresh",
    dependencies=[Depends(verify_csrf)],
)
async def refresh(
    response: Response,
    session: SessionDep,
    limiter: RateLimiterDep,
    settings: SettingsDep,
    client: ClientInfoDep,
    refresh_token: RefreshCookie = None,
) -> TokenRead:
    issued = await service.refresh(session, limiter, settings, client, refresh_token)
    _set_refresh_cookie(response, settings, issued.refresh_token, issued.refresh_expires_at)
    return issued.tokens


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="auth_logout",
    dependencies=[Depends(verify_csrf)],
)
async def logout(
    response: Response,
    session: SessionDep,
    settings: SettingsDep,
    client: ClientInfoDep,
    refresh_token: RefreshCookie = None,
) -> None:
    await service.logout(session, client, refresh_token)
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=MeRead, operation_id="auth_me")
async def me(session: SessionDep, actor: PendingPasswordActor) -> MeRead:
    return await service.me(session, actor)


@router.post(
    "/password/change",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="auth_password_change",
)
async def change_password(
    body: PasswordChangeIn,
    session: SessionDep,
    limiter: RateLimiterDep,
    actor: PendingPasswordActor,
    client: ClientInfoDep,
) -> None:
    await service.change_password(session, limiter, actor, client, body)


@router.post(
    "/password/forgot",
    status_code=status.HTTP_202_ACCEPTED,
    operation_id="auth_password_forgot",
)
async def forgot_password(
    body: PasswordForgotIn,
    session: SessionDep,
    limiter: RateLimiterDep,
    mailer: MailerDep,
    settings: SettingsDep,
    client: ClientInfoDep,
) -> None:
    await service.forgot_password(session, limiter, mailer, settings, client, body)


@router.post(
    "/password/reset",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="auth_password_reset",
)
async def reset_password(
    body: PasswordResetIn,
    session: SessionDep,
    limiter: RateLimiterDep,
    client: ClientInfoDep,
) -> None:
    await service.reset_password(session, limiter, client, body)
