"""Role x endpoint matrix for the users module."""

from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from tests.factories.users import SeededUser, bearer, create_user, login

Caller = Callable[[AsyncClient, dict[str, str], SeededUser, SeededUser], Awaitable[Response]]


async def _list(api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser) -> Response:
    return await api.get("/api/v1/users", headers=h)


async def _create(
    api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser
) -> Response:
    body = {"email": "new.user@example.com", "fullName": "Novo", "role": "teacher"}
    return await api.post("/api/v1/users", json=body, headers=h)


async def _get_other(
    api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser
) -> Response:
    return await api.get(f"/api/v1/users/{other.id}", headers=h)


async def _get_self(
    api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser
) -> Response:
    return await api.get(f"/api/v1/users/{me.id}", headers=h)


async def _rename_other(
    api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser
) -> Response:
    return await api.patch(f"/api/v1/users/{other.id}", json={"fullName": "X"}, headers=h)


async def _deactivate_other(
    api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser
) -> Response:
    return await api.post(f"/api/v1/users/{other.id}/deactivate", headers=h)


async def _activate_other(
    api: AsyncClient, h: dict[str, str], me: SeededUser, other: SeededUser
) -> Response:
    return await api.post(f"/api/v1/users/{other.id}/activate", headers=h)


# anonymous, teacher, admin
MATRIX: list[tuple[str, Caller, tuple[int, int, int]]] = [
    ("list", _list, (401, 403, 200)),
    ("create", _create, (401, 403, 201)),
    ("get other", _get_other, (401, 404, 200)),
    ("get self", _get_self, (401, 200, 200)),
    ("rename other", _rename_other, (401, 404, 200)),
    ("deactivate other", _deactivate_other, (401, 403, 200)),
    ("activate other", _activate_other, (401, 403, 200)),
]


@pytest.mark.parametrize(("name", "call", "expected"), MATRIX, ids=[m[0] for m in MATRIX])
@pytest.mark.parametrize("caller", ["anonymous", "teacher", "admin"])
async def test_users_authorization(
    api: AsyncClient,
    db_session: AsyncSession,
    name: str,
    call: Caller,
    expected: tuple[int, int, int],
    caller: str,
) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    teacher = await create_user(db_session, role=Role.TEACHER)
    other = await create_user(db_session, role=Role.TEACHER)

    me = {"anonymous": teacher, "teacher": teacher, "admin": admin}[caller]
    headers = {} if caller == "anonymous" else bearer(await login(api, me))

    response = await call(api, headers, me, other)

    status = expected[["anonymous", "teacher", "admin"].index(caller)]
    assert response.status_code == status, f"{name} as {caller}: {response.text}"
