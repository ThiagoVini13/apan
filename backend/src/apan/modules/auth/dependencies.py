"""Authentication and authorization dependencies used by every protected route."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apan.core.context import Actor, Role
from apan.core.dependencies import SessionDep, SettingsDep
from apan.core.errors import AuthenticationError, PermissionDeniedError
from apan.modules.auth import service

CSRF_HEADER = "X-Requested-With"
CSRF_HEADER_VALUE = "XMLHttpRequest"

_bearer = HTTPBearer(auto_error=False, description="Access token from POST /auth/login")
_WWW_AUTHENTICATE = {"WWW-Authenticate": "Bearer"}


async def get_actor_allowing_pending_password(
    session: SessionDep,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Actor:
    """Any authenticated user, including one who still has to change the password."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError(code="not_authenticated", headers=_WWW_AUTHENTICATE)
    try:
        return await service.authenticate(session, settings, credentials.credentials)
    except AuthenticationError as exc:
        exc.headers.update(_WWW_AUTHENTICATE)
        raise


async def get_actor(
    actor: Annotated[Actor, Depends(get_actor_allowing_pending_password)],
) -> Actor:
    if actor.must_change_password:
        raise PermissionDeniedError(code="password_change_required")
    return actor


def require_roles(*roles: Role) -> Callable[[Actor], Awaitable[Actor]]:
    allowed = frozenset(roles)

    async def dependency(actor: Annotated[Actor, Depends(get_actor)]) -> Actor:
        if actor.role not in allowed:
            raise PermissionDeniedError(code="permission_denied")
        return actor

    return dependency


def verify_csrf(request: Request, settings: SettingsDep) -> None:
    """For endpoints authenticated by cookie: custom header plus a trusted Origin."""
    if request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE:
        raise PermissionDeniedError(code="csrf_failed")
    origin = request.headers.get("origin")
    trusted = {*settings.cors_origins, settings.frontend_url.rstrip("/")}
    if origin is None or origin.rstrip("/") not in trusted:
        raise PermissionDeniedError(code="csrf_failed")


CurrentActor = Annotated[Actor, Depends(get_actor)]
PendingPasswordActor = Annotated[Actor, Depends(get_actor_allowing_pending_password)]
AdminActor = Annotated[Actor, Depends(require_roles(Role.ADMIN))]
