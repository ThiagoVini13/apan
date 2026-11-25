from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from tests.factories.users import UserCreateFactory, bearer, create_user, login

USERS = "/api/v1/users"


async def test_admin_lists_users_with_filters_and_pagination(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await create_user(db_session, role=Role.ADMIN, full_name="Ana Admin")
    await create_user(db_session, full_name="Bruno Professor")
    await create_user(db_session, full_name="Carla Professora", active=False)
    token = await login(api, admin)

    page = await api.get(USERS, params={"pageSize": 2}, headers=bearer(token))
    teachers = await api.get(
        USERS, params={"role": "teacher", "isActive": "true"}, headers=bearer(token)
    )
    search = await api.get(USERS, params={"q": "carla"}, headers=bearer(token))

    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert page.json()["pageSize"] == 2
    assert [u["fullName"] for u in page.json()["items"]] == ["Ana Admin", "Bruno Professor"]
    assert [u["fullName"] for u in teachers.json()["items"]] == ["Bruno Professor"]
    assert [u["fullName"] for u in search.json()["items"]] == ["Carla Professora"]


async def test_responses_never_expose_secrets(api: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    token = await login(api, admin)

    response = await api.get(f"{USERS}/{admin.id}", headers=bearer(token))

    keys = set(response.json())
    assert not keys & {"passwordHash", "password", "failedLoginCount", "lockedUntil"}


async def test_teacher_reads_only_own_profile(api: AsyncClient, db_session: AsyncSession) -> None:
    teacher = await create_user(db_session)
    other = await create_user(db_session)
    token = await login(api, teacher)

    own = await api.get(f"{USERS}/{teacher.id}", headers=bearer(token))
    foreign = await api.get(f"{USERS}/{other.id}", headers=bearer(token))

    assert own.status_code == 200
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "user_not_found"


async def test_teacher_updates_only_own_name(api: AsyncClient, db_session: AsyncSession) -> None:
    teacher = await create_user(db_session)
    other = await create_user(db_session)
    token = await login(api, teacher)

    renamed = await api.patch(
        f"{USERS}/{teacher.id}", json={"fullName": "  Nome Novo  "}, headers=bearer(token)
    )
    promote = await api.patch(
        f"{USERS}/{teacher.id}", json={"role": "admin"}, headers=bearer(token)
    )
    foreign = await api.patch(f"{USERS}/{other.id}", json={"fullName": "X"}, headers=bearer(token))

    assert renamed.status_code == 200
    assert renamed.json()["fullName"] == "Nome Novo"
    assert promote.status_code == 403
    assert foreign.status_code == 404


async def test_email_must_be_unique(api: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    teacher = await create_user(db_session)
    token = await login(api, admin)

    response = await api.patch(
        f"{USERS}/{teacher.id}", json={"email": admin.email.upper()}, headers=bearer(token)
    )
    duplicate = await api.post(
        USERS,
        json={"email": teacher.email, "fullName": "Outra", "role": "teacher"},
        headers=bearer(token),
    )

    assert response.status_code == duplicate.status_code == 409
    assert response.json()["fieldErrors"] == [{"field": "email", "code": "email_taken"}]


async def test_create_rejects_unknown_fields(api: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    token = await login(api, admin)
    payload = UserCreateFactory.build(role=Role.TEACHER).model_dump(by_alias=True, mode="json")

    response = await api.post(
        USERS,
        json={**payload, "passwordHash": "x", "isActive": False},
        headers=bearer(token),
    )

    assert response.status_code == 422
    assert {e["field"] for e in response.json()["fieldErrors"]} == {"passwordHash", "isActive"}


async def test_deactivate_and_activate(api: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    teacher = await create_user(db_session)
    admin_token = await login(api, admin)
    teacher_token = await login(api, teacher)

    deactivated = await api.post(f"{USERS}/{teacher.id}/deactivate", headers=bearer(admin_token))
    rejected = await api.get("/api/v1/auth/me", headers=bearer(teacher_token))
    activated = await api.post(f"{USERS}/{teacher.id}/activate", headers=bearer(admin_token))

    assert deactivated.json()["isActive"] is False
    assert rejected.status_code == 401
    assert activated.json()["isActive"] is True


async def test_admin_cannot_deactivate_self_or_remove_last_admin(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    token = await login(api, admin)

    deactivate_self = await api.post(f"{USERS}/{admin.id}/deactivate", headers=bearer(token))
    demote_self = await api.patch(
        f"{USERS}/{admin.id}", json={"role": "teacher"}, headers=bearer(token)
    )

    assert deactivate_self.status_code == 409
    assert deactivate_self.json()["code"] == "cannot_deactivate_self"
    assert demote_self.status_code == 409
    assert demote_self.json()["code"] == "last_admin"


async def test_admin_can_demote_another_admin_when_one_remains(
    api: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    other_admin = await create_user(db_session, role=Role.ADMIN)
    token = await login(api, admin)

    response = await api.patch(
        f"{USERS}/{other_admin.id}", json={"role": "teacher"}, headers=bearer(token)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "teacher"


async def test_role_change_applies_immediately(api: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    other_admin = await create_user(db_session, role=Role.ADMIN)
    admin_token = await login(api, admin)
    other_token = await login(api, other_admin)

    await api.patch(
        f"{USERS}/{other_admin.id}", json={"role": "teacher"}, headers=bearer(admin_token)
    )
    response = await api.get(USERS, headers=bearer(other_token))

    assert response.status_code == 403


async def test_unknown_user_returns_not_found(api: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_user(db_session, role=Role.ADMIN)
    token = await login(api, admin)

    response = await api.get(f"{USERS}/00000000-0000-7000-8000-000000000000", headers=bearer(token))

    assert response.status_code == 404
