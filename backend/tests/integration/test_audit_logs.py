from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from tests.factories.registries import Seed
from tests.factories.users import bearer, create_user, login


async def test_admin_lists_audit_logs_with_filters(api: AsyncClient, seed: Seed) -> None:
    await seed.subject(name="Artes")

    everything = await api.get("/api/v1/audit-logs", headers=seed.headers)
    subjects = await api.get(
        "/api/v1/audit-logs", params={"action": "subjects."}, headers=seed.headers
    )

    assert everything.status_code == 200
    assert everything.json()["items"][0]["action"] == "subjects.created"
    assert everything.json()["items"][0]["actorName"] == "Pessoa de Teste"
    assert [e["action"] for e in subjects.json()["items"]] == ["subjects.created"]


async def test_audit_logs_are_admin_only(api: AsyncClient, db_session: AsyncSession) -> None:
    teacher = await create_user(db_session, role=Role.TEACHER)
    response = await api.get("/api/v1/audit-logs", headers=bearer(await login(api, teacher)))

    assert response.status_code == 403
