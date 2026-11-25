"""Roll calls. "Today" is frozen at Tuesday 2026-11-24 (see conftest)."""

from dataclasses import dataclass
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.modules.audit.models import AuditLog
from tests.factories.registries import Seed

ROLL_CALLS = "/api/v1/roll-calls"
MONDAY = "2026-11-23"


@dataclass
class Lesson:
    year: dict[str, Any]
    school_class: dict[str, Any]
    subject: dict[str, Any]
    teacher: dict[str, str]
    students: list[dict[str, Any]]

    def body(self, marks: dict[str, str] | None = None, **overrides: Any) -> dict[str, Any]:
        marks = marks or {}
        return {
            "classId": self.school_class["id"],
            "subjectId": self.subject["id"],
            "lessonDate": MONDAY,
            "attendances": [
                {"studentId": s["id"], "status": marks.get(s["fullName"], "present")}
                for s in self.students
            ],
            **overrides,
        }


async def _lesson(seed: Seed) -> Lesson:
    year = await seed.year()
    school_class = await seed.school_class(year["id"], name="5º Ano A")
    subject = await seed.subject(name="Matemática")
    _, teacher = await seed.teacher_in_class(school_class["id"], subject["id"])
    students = [
        await seed.student(school_class["id"], full_name=name, enrolled_on="2026-03-02")
        for name in ("Carla", "Alice", "Bruno")
    ]
    return Lesson(year, school_class, subject, teacher, students)


def _sheet_params(lesson: Lesson, day: str = MONDAY) -> dict[str, str]:
    return {"classId": lesson.school_class["id"], "subjectId": lesson.subject["id"], "date": day}


async def test_sheet_lists_the_roster_for_the_day(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)

    response = await api.get(
        f"{ROLL_CALLS}/sheet", params=_sheet_params(lesson), headers=lesson.teacher
    )

    body = response.json()
    assert response.status_code == 200
    assert body["rollCallId"] is None
    assert body["isSchoolDay"] is True
    assert body["editable"] is True
    assert [s["fullName"] for s in body["students"]] == ["Alice", "Bruno", "Carla"]
    assert {s["status"] for s in body["students"]} == {None}


async def test_teacher_takes_and_corrects_a_roll_call(
    api: AsyncClient, db_session: AsyncSession, seed: Seed
) -> None:
    lesson = await _lesson(seed)

    first = await api.put(
        ROLL_CALLS,
        json=lesson.body({"Bruno": "absent"}, notes="  Frações e porcentagem.  "),
        headers=lesson.teacher,
    )
    second = await api.put(
        ROLL_CALLS,
        json=lesson.body(
            {"Bruno": "present", "Carla": "absent"}, notes="Frações; Carla saiu cedo."
        ),
        headers=lesson.teacher,
    )
    sheet = await api.get(
        f"{ROLL_CALLS}/sheet", params=_sheet_params(lesson), headers=lesson.teacher
    )

    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["notes"] == "Frações e porcentagem."
    assert (first.json()["presentCount"], first.json()["absentCount"]) == (2, 1)
    assert second.json()["notes"] == "Frações; Carla saiu cedo."
    marks = {s["fullName"]: s["status"] for s in sheet.json()["students"]}
    assert marks == {"Alice": "present", "Bruno": "present", "Carla": "absent"}
    assert sheet.json()["rollCallId"] == first.json()["id"]

    actions = (
        await db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_id == first.json()["id"])
        )
    ).scalars()
    assert sorted(actions) == ["roll_calls.created", "roll_calls.updated"]


async def test_roll_call_must_match_the_roster(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)
    other_class = await seed.school_class(lesson.year["id"], name="Outra")
    stranger = await seed.student(other_class["id"], enrolled_on="2026-03-02")
    body = lesson.body()

    incomplete = await api.put(
        ROLL_CALLS, json={**body, "attendances": body["attendances"][:2]}, headers=lesson.teacher
    )
    extra = await api.put(
        ROLL_CALLS,
        json={
            **body,
            "attendances": [
                *body["attendances"],
                {"studentId": stranger["id"], "status": "present"},
            ],
        },
        headers=lesson.teacher,
    )
    duplicate = await api.put(
        ROLL_CALLS,
        json={**body, "attendances": [*body["attendances"], body["attendances"][0]]},
        headers=lesson.teacher,
    )

    assert incomplete.json()["code"] == "roll_call_incomplete"
    assert extra.json()["code"] == "student_not_enrolled"
    assert duplicate.json()["code"] == "duplicate_student"
    assert incomplete.status_code == extra.status_code == duplicate.status_code == 422


async def test_lesson_date_rules(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)
    await api.post(
        f"/api/v1/school-years/{lesson.year['id']}/calendar-days",
        json={"day": "2026-11-20", "kind": "holiday"},
        headers=seed.headers,
    )
    await api.post(
        f"/api/v1/school-years/{lesson.year['id']}/calendar-days",
        json={"day": "2026-11-21", "kind": "extra_school_day"},
        headers=seed.headers,
    )

    async def put(day: str) -> dict[str, Any]:
        response = await api.put(
            ROLL_CALLS, json=lesson.body(lessonDate=day), headers=lesson.teacher
        )
        return {"status": response.status_code, **response.json()}

    future = await put("2026-11-25")
    sunday = await put("2026-11-22")
    holiday = await put("2026-11-20")
    saturday_class = await put("2026-11-21")
    outside_year = await put("2026-01-15")

    assert (future["status"], future["code"]) == (422, "lesson_in_future")
    assert (sunday["status"], sunday["code"]) == (422, "not_a_school_day")
    assert (holiday["status"], holiday["code"]) == (422, "not_a_school_day")
    assert saturday_class["status"] == 200
    assert (outside_year["status"], outside_year["code"]) == (422, "date_outside_school_year")


async def test_edit_window_limits_teachers_but_not_admins(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)
    old = lesson.body(lessonDate="2026-11-10")

    teacher = await api.put(ROLL_CALLS, json=old, headers=lesson.teacher)
    admin = await api.put(ROLL_CALLS, json=old, headers=seed.headers)
    sheet = await api.get(
        f"{ROLL_CALLS}/sheet", params=_sheet_params(lesson, "2026-11-10"), headers=lesson.teacher
    )
    edge = await api.put(
        ROLL_CALLS, json=lesson.body(lessonDate="2026-11-17"), headers=lesson.teacher
    )

    assert teacher.status_code == 409
    assert teacher.json()["code"] == "roll_call_locked"
    assert admin.status_code == 200
    assert sheet.json()["editable"] is False
    assert edge.status_code == 200


async def test_teacher_only_takes_roll_for_own_subjects_and_classes(
    api: AsyncClient, seed: Seed
) -> None:
    lesson = await _lesson(seed)
    other_subject = await seed.subject(name="Ciências")
    other_class = await seed.school_class(lesson.year["id"], name="Outra")

    wrong_subject = await api.put(
        ROLL_CALLS, json=lesson.body(subjectId=other_subject["id"]), headers=lesson.teacher
    )
    wrong_class = await api.put(
        ROLL_CALLS, json=lesson.body(classId=other_class["id"]), headers=lesson.teacher
    )

    assert wrong_subject.status_code == 403
    assert wrong_subject.json()["code"] == "subject_not_assigned"
    assert wrong_class.status_code == 404


async def test_roster_follows_enrollment_dates(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)
    newcomer = await seed.student(
        lesson.school_class["id"], full_name="Davi", enrolled_on="2026-11-24"
    )
    target = await seed.school_class(lesson.year["id"], name="Destino")
    await api.post(
        f"/api/v1/enrollments/{lesson.students[0]['currentEnrollmentId']}/transfer",
        json={"classId": target["id"], "transferOn": "2026-11-24"},
        headers=seed.headers,
    )

    monday = await api.get(
        f"{ROLL_CALLS}/sheet", params=_sheet_params(lesson), headers=lesson.teacher
    )
    tuesday = await api.get(
        f"{ROLL_CALLS}/sheet", params=_sheet_params(lesson, "2026-11-24"), headers=lesson.teacher
    )

    assert [s["fullName"] for s in monday.json()["students"]] == ["Alice", "Bruno", "Carla"]
    assert [s["fullName"] for s in tuesday.json()["students"]] == ["Alice", "Bruno", "Davi"]
    assert newcomer["currentClassId"] == lesson.school_class["id"]


async def test_archived_class_cannot_receive_roll_calls(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)
    await api.post(f"/api/v1/classes/{lesson.school_class['id']}/archive", headers=seed.headers)

    response = await api.put(ROLL_CALLS, json=lesson.body(), headers=seed.headers)

    assert response.status_code == 409
    assert response.json()["code"] == "class_archived"


async def test_notes_are_limited_to_1000_characters(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)

    response = await api.put(ROLL_CALLS, json=lesson.body(notes="x" * 1001), headers=lesson.teacher)

    assert response.status_code == 422


async def test_list_is_scoped_and_filterable(api: AsyncClient, seed: Seed) -> None:
    lesson = await _lesson(seed)
    other_class = await seed.school_class(lesson.year["id"], name="Outra")
    await seed.student(other_class["id"], enrolled_on="2026-03-02")
    await api.put(ROLL_CALLS, json=lesson.body(), headers=lesson.teacher)
    await api.put(ROLL_CALLS, json=lesson.body(lessonDate="2026-11-24"), headers=lesson.teacher)
    other_marks = (
        await api.get(
            f"{ROLL_CALLS}/sheet",
            params={
                "classId": other_class["id"],
                "subjectId": lesson.subject["id"],
                "date": MONDAY,
            },
            headers=seed.headers,
        )
    ).json()["students"]
    await api.put(
        ROLL_CALLS,
        json={
            "classId": other_class["id"],
            "subjectId": lesson.subject["id"],
            "lessonDate": MONDAY,
            "attendances": [
                {"studentId": s["studentId"], "status": "present"} for s in other_marks
            ],
        },
        headers=seed.headers,
    )

    teacher_list = await api.get(ROLL_CALLS, headers=lesson.teacher)
    admin_monday = await api.get(ROLL_CALLS, params={"date": MONDAY}, headers=seed.headers)

    assert teacher_list.json()["total"] == 2
    assert {r["classId"] for r in teacher_list.json()["items"]} == {lesson.school_class["id"]}
    assert admin_monday.json()["total"] == 2
