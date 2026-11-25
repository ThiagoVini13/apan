import re

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.modules.audit.models import AuditLog
from tests.factories.registries import DEFAULT_GUARDIAN, Seed

STUDENTS = "/api/v1/students"


async def _class_with_teacher(seed: Seed) -> tuple[dict[str, str], dict[str, str]]:
    year = await seed.year()
    school_class = await seed.school_class(year["id"])
    subject = await seed.subject()
    _, teacher = await seed.teacher_in_class(school_class["id"], subject["id"])
    return school_class, teacher


async def test_teacher_registers_student_into_own_class(api: AsyncClient, seed: Seed) -> None:
    school_class, teacher = await _class_with_teacher(seed)

    student = await seed.student(school_class["id"], full_name="Alice Souza", headers=teacher)

    assert re.fullmatch(r"2026\d{5}", student["enrollmentNumber"])
    assert student["currentClassId"] == school_class["id"]
    assert student["guardians"][0]["phone"] == "92991234567"
    assert student["guardians"][0]["isPrimary"] is True
    listed = await api.get(f"/api/v1/classes/{school_class['id']}/students", headers=teacher)
    assert [s["fullName"] for s in listed.json()["items"]] == ["Alice Souza"]


async def test_teacher_must_pick_one_of_own_classes(api: AsyncClient, seed: Seed) -> None:
    school_class, teacher = await _class_with_teacher(seed)
    other = await seed.school_class(school_class["schoolYearId"], name="Outra")
    body = {"fullName": "Bruno", "birthDate": "2016-01-01", "guardians": [DEFAULT_GUARDIAN]}

    without_class = await api.post(STUDENTS, json=body, headers=teacher)
    foreign_class = await api.post(STUDENTS, json={**body, "classId": other["id"]}, headers=teacher)

    assert without_class.status_code == 422
    assert without_class.json()["code"] == "class_required"
    assert foreign_class.status_code == 404


async def test_student_validation_rules(api: AsyncClient, seed: Seed) -> None:
    async def create(**overrides: object) -> dict[str, object]:
        body = {"fullName": "Carla", "birthDate": "2016-01-01", "guardians": [DEFAULT_GUARDIAN]}
        response = await api.post(STUDENTS, json={**body, **overrides}, headers=seed.headers)
        assert response.status_code == 422, response.text
        result: dict[str, object] = response.json()
        return result

    minor_alone = await create(guardians=[])
    too_young = await create(birthDate="2025-01-01")
    future = await create(birthDate="2030-01-01")
    bad_phone = await create(guardians=[{**DEFAULT_GUARDIAN, "phone": "1234"}])
    two_primaries = await create(
        guardians=[{**DEFAULT_GUARDIAN, "isPrimary": True}, {**DEFAULT_GUARDIAN, "isPrimary": True}]
    )

    assert minor_alone["code"] == "guardian_required"
    assert too_young["code"] == "student_too_young"
    assert future["code"] == "date_in_future"
    assert bad_phone["fieldErrors"] == [{"field": "guardians.0.phone", "code": "invalid_phone"}]
    assert two_primaries["code"] == "multiple_primary_guardians"


async def test_adult_student_needs_no_guardian(seed: Seed) -> None:
    student = await seed.student(birth_date="2000-05-10", guardians=[])

    assert student["guardians"] == []
    assert student["currentClassId"] is None


async def test_teacher_cannot_reach_students_of_other_classes(api: AsyncClient, seed: Seed) -> None:
    school_class, teacher = await _class_with_teacher(seed)
    other = await seed.school_class(school_class["schoolYearId"], name="Outra")
    mine = await seed.student(school_class["id"], full_name="Meu Aluno")
    foreign = await seed.student(other["id"], full_name="Aluno Alheio")

    listed = await api.get(STUDENTS, headers=teacher)
    get_foreign = await api.get(f"{STUDENTS}/{foreign['id']}", headers=teacher)
    patch_foreign = await api.patch(
        f"{STUDENTS}/{foreign['id']}", json={"fullName": "X"}, headers=teacher
    )
    guardians_foreign = await api.get(f"{STUDENTS}/{foreign['id']}/guardians", headers=teacher)
    patch_mine = await api.patch(
        f"{STUDENTS}/{mine['id']}", json={"fullName": "Meu Aluno Corrigido"}, headers=teacher
    )

    assert [s["fullName"] for s in listed.json()["items"]] == ["Meu Aluno"]
    assert get_foreign.status_code == patch_foreign.status_code == 404
    assert guardians_foreign.status_code == 404
    assert patch_mine.json()["fullName"] == "Meu Aluno Corrigido"


async def test_admin_reading_a_record_is_audited(
    api: AsyncClient, db_session: AsyncSession, seed: Seed
) -> None:
    student = await seed.student()

    await api.get(f"{STUDENTS}/{student['id']}", headers=seed.headers)

    actions = (
        await db_session.execute(select(AuditLog.action).where(AuditLog.entity_id == student["id"]))
    ).scalars()
    assert set(actions) == {"students.created", "students.viewed"}


async def test_archiving_ends_enrollment_and_hides_the_student(
    api: AsyncClient, seed: Seed
) -> None:
    school_class, teacher = await _class_with_teacher(seed)
    student = await seed.student(school_class["id"], enrolled_on="2026-03-02")

    archived = await api.post(f"{STUDENTS}/{student['id']}/archive", headers=seed.headers)
    default_list = await api.get(STUDENTS, headers=seed.headers)
    with_archived = await api.get(
        STUDENTS, params={"includeArchived": "true"}, headers=seed.headers
    )
    teacher_view = await api.get(f"{STUDENTS}/{student['id']}", headers=teacher)
    enrollment = await api.get(
        f"/api/v1/enrollments/{student['currentEnrollmentId']}", headers=seed.headers
    )

    assert archived.json()["archivedAt"] is not None
    assert archived.json()["currentClassId"] is None
    assert default_list.json()["total"] == 0
    assert with_archived.json()["total"] == 1
    assert teacher_view.status_code == 404
    assert enrollment.json()["status"] == "cancelled"


async def test_guardian_rules(api: AsyncClient, seed: Seed) -> None:
    student = await seed.student()
    url = f"{STUDENTS}/{student['id']}/guardians"
    first_id = student["guardians"][0]["id"]

    second = await api.post(
        url,
        json={
            "fullName": "João Pai",
            "phone": "92 3234-5678",
            "relationship": "father",
            "isPrimary": True,
        },
        headers=seed.headers,
    )
    after_add = (await api.get(url, headers=seed.headers)).json()["items"]
    removed_primary = await api.delete(f"{url}/{second.json()['id']}", headers=seed.headers)
    after_remove = (await api.get(url, headers=seed.headers)).json()["items"]
    remove_last = await api.delete(f"{url}/{first_id}", headers=seed.headers)

    assert [(g["fullName"], g["isPrimary"]) for g in after_add] == [
        ("João Pai", True),
        ("Maria Responsável", False),
    ]
    assert removed_primary.status_code == 204
    assert [(g["id"], g["isPrimary"]) for g in after_remove] == [(first_id, True)]
    assert remove_last.status_code == 409
    assert remove_last.json()["code"] == "guardian_required"


async def test_becoming_a_minor_requires_a_guardian(api: AsyncClient, seed: Seed) -> None:
    adult = await seed.student(birth_date="2000-05-10", guardians=[])

    response = await api.patch(
        f"{STUDENTS}/{adult['id']}", json={"birthDate": "2015-05-10"}, headers=seed.headers
    )

    assert response.status_code == 409
    assert response.json()["code"] == "guardian_required"


async def test_search_by_name_or_number(api: AsyncClient, seed: Seed) -> None:
    alice = await seed.student(full_name="Alice Souza")
    await seed.student(full_name="Bruno Lima")

    by_name = await api.get(STUDENTS, params={"q": "souza"}, headers=seed.headers)
    by_number = await api.get(
        STUDENTS, params={"q": alice["enrollmentNumber"]}, headers=seed.headers
    )

    assert [s["fullName"] for s in by_name.json()["items"]] == ["Alice Souza"]
    assert [s["fullName"] for s in by_number.json()["items"]] == ["Alice Souza"]
