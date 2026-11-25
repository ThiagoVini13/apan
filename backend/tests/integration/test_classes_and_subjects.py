from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apan.core.context import Role
from tests.factories.registries import Seed
from tests.factories.users import create_user

CLASSES = "/api/v1/classes"


async def test_subject_codes_are_normalized_and_unique(api: AsyncClient, seed: Seed) -> None:
    created = await api.post(
        "/api/v1/subjects", json={"code": " mat ", "name": "Matemática"}, headers=seed.headers
    )
    duplicate = await api.post(
        "/api/v1/subjects", json={"code": "MAT", "name": "Outra"}, headers=seed.headers
    )

    assert created.json()["code"] == "MAT"
    assert duplicate.status_code == 409


async def test_subject_in_use_cannot_be_deleted(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    school_class = await seed.school_class(year["id"])
    subject = await seed.subject()
    await seed.teacher_in_class(school_class["id"], subject["id"])

    response = await api.delete(f"/api/v1/subjects/{subject['id']}", headers=seed.headers)

    assert response.status_code == 409
    assert response.json()["code"] == "subject_in_use"


async def test_class_names_are_unique_per_year_and_shift(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    await seed.school_class(year["id"], name="5º Ano A", shift="morning")
    afternoon = await seed.school_class(year["id"], name="5º Ano A", shift="afternoon")

    duplicate = await api.post(
        CLASSES,
        json={"schoolYearId": year["id"], "name": "5º ano a", "grade": "5", "shift": "morning"},
        headers=seed.headers,
    )

    assert afternoon["shift"] == "afternoon"
    assert duplicate.status_code == 409


async def test_class_requires_existing_year(api: AsyncClient, seed: Seed) -> None:
    response = await api.post(
        CLASSES,
        json={
            "schoolYearId": "00000000-0000-7000-8000-000000000000",
            "name": "X",
            "grade": "5",
            "shift": "morning",
        },
        headers=seed.headers,
    )

    assert response.status_code == 422
    assert response.json()["fieldErrors"] == [
        {"field": "schoolYearId", "code": "school_year_not_found"}
    ]


async def test_teacher_sees_only_assigned_classes(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    mine = await seed.school_class(year["id"], name="Minha")
    other = await seed.school_class(year["id"], name="Outra")
    subject = await seed.subject()
    _, teacher = await seed.teacher_in_class(mine["id"], subject["id"])

    listed = await api.get(CLASSES, headers=teacher)
    foreign = await api.get(f"{CLASSES}/{other['id']}", headers=teacher)
    foreign_students = await api.get(f"{CLASSES}/{other['id']}/students", headers=teacher)
    own_teachers = await api.get(f"{CLASSES}/{mine['id']}/subject-teachers", headers=teacher)

    assert [c["name"] for c in listed.json()["items"]] == ["Minha"]
    assert foreign.status_code == 404
    assert foreign_students.status_code == 404
    assert own_teachers.status_code == 200


async def test_subject_teacher_assignment_validation(
    api: AsyncClient, db_session: AsyncSession, seed: Seed
) -> None:
    year = await seed.year()
    school_class = await seed.school_class(year["id"])
    subject = await seed.subject(name="Português")
    teacher = await create_user(db_session, role=Role.TEACHER, full_name="Prof. Ana")
    url = f"{CLASSES}/{school_class['id']}/subject-teachers"

    invalid = await api.put(
        url,
        json={
            "items": [
                {"subjectId": subject["id"], "teacherId": str(seed.admin.id)},
                {"subjectId": subject["id"], "teacherId": str(teacher.id)},
            ]
        },
        headers=seed.headers,
    )
    valid = await seed.assign(school_class["id"], [(subject["id"], teacher.id)])

    assert invalid.status_code == 422
    assert {(e["field"], e["code"]) for e in invalid.json()["fieldErrors"]} == {
        ("items.0.teacherId", "teacher_not_found"),
        ("items.1.subjectId", "duplicate_subject"),
    }
    assert valid["items"] == [
        {
            "subjectId": subject["id"],
            "subjectName": "Português",
            "subjectCode": subject["code"],
            "teacherId": str(teacher.id),
            "teacherName": "Prof. Ana",
        }
    ]


async def test_capacity_cannot_drop_below_enrollments(api: AsyncClient, seed: Seed) -> None:
    year = await seed.year()
    school_class = await seed.school_class(year["id"], capacity=5)
    await seed.student(school_class["id"])
    await seed.student(school_class["id"])

    shrink = await api.patch(
        f"{CLASSES}/{school_class['id']}", json={"capacity": 1}, headers=seed.headers
    )
    read = await api.get(f"{CLASSES}/{school_class['id']}", headers=seed.headers)

    assert shrink.status_code == 409
    assert read.json()["studentCount"] == 2
