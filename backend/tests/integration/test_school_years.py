from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from tests.factories.registries import Seed
from tests.factories.users import bearer, create_user, login

YEARS = "/api/v1/school-years"


async def test_create_and_read_school_year(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year(name="2026")

    response = await api.get(f"{YEARS}/{year['id']}", headers=seed.headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": year["id"],
        "name": "2026",
        "startsOn": "2026-02-01",
        "endsOn": "2026-12-15",
        "isCurrent": True,
    }


async def test_only_one_current_year(api: AsyncClient, seed: Seed) -> None:
    first = await seed.year(name="2025", starts_on="2025-02-01", ends_on="2025-12-15")
    second = await seed.year(name="2026")

    listed = (await api.get(YEARS, headers=seed.headers)).json()["items"]

    current = {y["id"]: y["isCurrent"] for y in listed}
    assert current == {first["id"]: False, second["id"]: True}


async def test_rejects_invalid_or_duplicate_years(api: AsyncClient, seed: Seed) -> None:
    await seed.year(name="2026")

    inverted = await api.post(
        YEARS,
        json={"name": "X", "startsOn": "2026-12-01", "endsOn": "2026-02-01"},
        headers=seed.headers,
    )
    duplicate = await api.post(
        YEARS,
        json={"name": "2026", "startsOn": "2026-02-01", "endsOn": "2026-12-15"},
        headers=seed.headers,
    )

    assert inverted.status_code == 422
    assert inverted.json()["code"] == "invalid_date_range"
    assert duplicate.status_code == 409


async def test_terms_must_fit_the_year_and_not_overlap(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    url = f"{YEARS}/{year['id']}/terms"

    first = await api.post(
        url,
        json={"name": "1º bimestre", "startsOn": "2026-02-01", "endsOn": "2026-04-30"},
        headers=seed.headers,
    )
    overlap = await api.post(
        url,
        json={"name": "2º bimestre", "startsOn": "2026-04-15", "endsOn": "2026-07-10"},
        headers=seed.headers,
    )
    outside = await api.post(
        url,
        json={"name": "Férias", "startsOn": "2026-12-20", "endsOn": "2026-12-31"},
        headers=seed.headers,
    )
    listed = await api.get(url, headers=seed.headers)

    assert first.status_code == 201
    assert overlap.status_code == 409
    assert overlap.json()["code"] == "term_overlaps"
    assert outside.status_code == 422
    assert outside.json()["code"] == "date_outside_school_year"
    assert listed.json()["total"] == 1


async def test_calendar_days(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    url = f"{YEARS}/{year['id']}/calendar-days"
    holiday = {"day": "2026-11-20", "kind": "holiday", "description": "Consciência Negra"}

    created = await api.post(url, json=holiday, headers=seed.headers)
    duplicate = await api.post(url, json=holiday, headers=seed.headers)
    outside = await api.post(url, json={**holiday, "day": "2027-01-01"}, headers=seed.headers)
    deleted = await api.delete(f"{url}/{created.json()['id']}", headers=seed.headers)

    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert outside.status_code == 422
    assert deleted.status_code == 204


async def test_year_in_use_cannot_be_deleted(api: AsyncClient, seed: Seed) -> None:
    used = await seed.year(name="Usado")
    unused = await seed.year(name="Livre", is_current=False)
    await seed.school_class(used["id"])

    blocked = await api.delete(f"{YEARS}/{used['id']}", headers=seed.headers)
    removed = await api.delete(f"{YEARS}/{unused['id']}", headers=seed.headers)

    assert blocked.status_code == 409
    assert blocked.json()["code"] == "school_year_in_use"
    assert removed.status_code == 204


async def test_teacher_reads_but_cannot_change_school_years(
    api: AsyncClient, db_session: AsyncSession, seed: Seed
) -> None:
    year = await seed.year()
    teacher = bearer(await login(api, await create_user(db_session, role=Role.TEACHER)))

    read = await api.get(f"{YEARS}/{year['id']}/terms", headers=teacher)
    write = await api.patch(f"{YEARS}/{year['id']}", json={"name": "X"}, headers=teacher)

    assert read.status_code == 200
    assert write.status_code == 403
