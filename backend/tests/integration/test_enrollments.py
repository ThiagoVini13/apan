from httpx import AsyncClient

from tests.factories.registries import Seed

ENROLLMENTS = "/api/v1/enrollments"


async def test_one_active_enrollment_per_student_per_year(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    first = await seed.school_class(year["id"], name="A")
    second = await seed.school_class(year["id"], name="B")
    student = await seed.student(first["id"])

    response = await api.post(
        ENROLLMENTS,
        json={"studentId": student["id"], "classId": second["id"]},
        headers=seed.headers,
    )

    assert response.status_code == 409
    assert response.json()["code"] == "student_already_enrolled"


async def test_enrollment_into_next_year_is_allowed(api: AsyncClient, seed: Seed) -> None:
    this_year = await seed.year(name="2026")
    next_year = await seed.year(
        name="2027", starts_on="2027-02-01", ends_on="2027-12-15", is_current=False
    )
    current = await seed.school_class(this_year["id"])
    upcoming = await seed.school_class(next_year["id"])
    student = await seed.student(current["id"])

    response = await api.post(
        ENROLLMENTS,
        json={"studentId": student["id"], "classId": upcoming["id"]},
        headers=seed.headers,
    )

    assert response.status_code == 201
    assert response.json()["startsOn"] == "2027-02-01"


async def test_capacity_and_archived_classes(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    tiny = await seed.school_class(year["id"], name="Pequena", capacity=1)
    archived = await seed.school_class(year["id"], name="Arquivada")
    await api.post(f"/api/v1/classes/{archived['id']}/archive", headers=seed.headers)
    await seed.student(tiny["id"])
    second = await seed.student()

    full = await api.post(
        ENROLLMENTS, json={"studentId": second["id"], "classId": tiny["id"]}, headers=seed.headers
    )
    closed = await api.post(
        ENROLLMENTS,
        json={"studentId": second["id"], "classId": archived["id"]},
        headers=seed.headers,
    )

    assert full.status_code == 409
    assert full.json()["code"] == "class_capacity_exceeded"
    assert closed.status_code == 409
    assert closed.json()["code"] == "class_archived"


async def test_enrollment_dates_must_fall_in_the_school_year(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    school_class = await seed.school_class(year["id"])
    student = await seed.student()

    response = await api.post(
        ENROLLMENTS,
        json={"studentId": student["id"], "classId": school_class["id"], "startsOn": "2027-01-10"},
        headers=seed.headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "date_outside_school_year"


async def test_transfer_between_classes(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    origin = await seed.school_class(year["id"], name="Origem")
    target = await seed.school_class(year["id"], name="Destino")
    other_year = await seed.year(
        name="2027", starts_on="2027-02-01", ends_on="2027-12-15", is_current=False
    )
    elsewhere = await seed.school_class(other_year["id"])
    student = await seed.student(origin["id"], enrolled_on="2026-03-02")
    enrollment_id = student["currentEnrollmentId"]
    url = f"{ENROLLMENTS}/{enrollment_id}/transfer"

    same = await api.post(url, json={"classId": origin["id"]}, headers=seed.headers)
    wrong_year = await api.post(url, json={"classId": elsewhere["id"]}, headers=seed.headers)
    too_early = await api.post(
        url, json={"classId": target["id"], "transferOn": "2026-03-02"}, headers=seed.headers
    )
    moved = await api.post(
        url, json={"classId": target["id"], "transferOn": "2026-08-03"}, headers=seed.headers
    )
    old = await api.get(f"{ENROLLMENTS}/{enrollment_id}", headers=seed.headers)
    again = await api.post(url, json={"classId": target["id"]}, headers=seed.headers)

    assert same.status_code == wrong_year.status_code == too_early.status_code == 422
    assert moved.status_code == 200
    assert (moved.json()["classId"], moved.json()["startsOn"]) == (target["id"], "2026-08-03")
    assert (old.json()["status"], old.json()["endsOn"]) == ("transferred", "2026-08-02")
    assert again.status_code == 409
    assert again.json()["code"] == "enrollment_not_active"


async def test_cancel_enrollment(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    school_class = await seed.school_class(year["id"])
    student = await seed.student(school_class["id"], enrolled_on="2026-03-02")
    url = f"{ENROLLMENTS}/{student['currentEnrollmentId']}/cancel"

    before_start = await api.post(url, json={"endsOn": "2026-03-01"}, headers=seed.headers)
    cancelled = await api.post(url, json={"endsOn": "2026-06-30"}, headers=seed.headers)
    count = await api.get(f"/api/v1/classes/{school_class['id']}", headers=seed.headers)

    assert before_start.status_code == 422
    assert (cancelled.json()["status"], cancelled.json()["endsOn"]) == ("cancelled", "2026-06-30")
    assert count.json()["studentCount"] == 0


async def test_teacher_sees_only_enrollments_of_own_classes(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    mine = await seed.school_class(year["id"], name="Minha")
    other = await seed.school_class(year["id"], name="Outra")
    subject = await seed.subject()
    _, teacher = await seed.teacher_in_class(mine["id"], subject["id"])
    await seed.student(mine["id"])
    foreign = await seed.student(other["id"])

    listed = await api.get(ENROLLMENTS, headers=teacher)
    foreign_get = await api.get(f"{ENROLLMENTS}/{foreign['currentEnrollmentId']}", headers=teacher)

    assert {e["classId"] for e in listed.json()["items"]} == {mine["id"]}
    assert foreign_get.status_code == 404
