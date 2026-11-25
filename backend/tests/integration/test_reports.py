"""Period reports and spreadsheet export."""

import csv
import io
import zipfile
from dataclasses import dataclass
from typing import Any

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apan.modules.audit.models import AuditLog
from tests.factories.registries import Seed

REPORTS = "/api/v1/reports/attendance"
PERIOD = {"from": "2026-11-01", "to": "2026-11-30"}
# Mon..Fri of the week of 2026-11-16, plus Monday 23.
LESSON_DAYS = ["2026-11-16", "2026-11-17", "2026-11-18", "2026-11-19", "2026-11-23"]


@dataclass
class World:
    year: dict[str, Any]
    subject: dict[str, Any]
    class_a: dict[str, Any]
    class_b: dict[str, Any]
    teacher_a: dict[str, str]
    students: dict[str, dict[str, Any]]


async def _take(
    api: AsyncClient,
    seed: Seed,
    school_class: dict[str, Any],
    subject_id: str,
    day: str,
    absent: set[str],
    students: dict[str, dict[str, Any]],
    notes: str | None = None,
) -> None:
    members = [s for s in students.values() if s["currentClassId"] == school_class["id"]]
    response = await api.put(
        "/api/v1/roll-calls",
        json={
            "classId": school_class["id"],
            "subjectId": subject_id,
            "lessonDate": day,
            "notes": notes,
            "attendances": [
                {"studentId": s["id"], "status": "absent" if s["fullName"] in absent else "present"}
                for s in members
            ],
        },
        headers=seed.headers,
    )
    assert response.status_code == 200, response.text


async def _world(api: AsyncClient, seed: Seed) -> World:
    year = await seed.year()
    subject = await seed.subject(name="Matemática")
    class_a = await seed.school_class(year["id"], name="5º Ano A")
    class_b = await seed.school_class(year["id"], name="6º Ano B")
    _, teacher_a = await seed.teacher_in_class(class_a["id"], subject["id"])
    await seed.teacher_in_class(class_b["id"], subject["id"])
    students = {}
    for name, school_class in [("Ana", class_a), ("=1+1 Bia", class_a), ("Caio", class_b)]:
        students[name] = await seed.student(
            school_class["id"], full_name=name, enrolled_on="2026-03-02"
        )

    # Ana: always present (5/5). Bia: absent 2 of 5 (60%). Caio: absent 1 of 4 (75%).
    for index, day in enumerate(LESSON_DAYS):
        absent_a = {"=1+1 Bia"} if index in (1, 3) else set()
        await _take(
            api, seed, class_a, subject["id"], day, absent_a, students, notes=f"Aula {index + 1}"
        )
    for index, day in enumerate(LESSON_DAYS[:4]):
        await _take(
            api, seed, class_b, subject["id"], day, {"Caio"} if index == 0 else set(), students
        )
    return World(year, subject, class_a, class_b, teacher_a, students)


async def test_report_by_student(api: AsyncClient, seed: Seed) -> None:
    await _world(api, seed)

    response = await api.get(f"{REPORTS}/students", params=PERIOD, headers=seed.headers)

    rows = {r["fullName"]: r for r in response.json()["items"]}
    assert [r["fullName"] for r in response.json()["items"]] == ["=1+1 Bia", "Ana", "Caio"]
    assert (rows["Ana"]["present"], rows["Ana"]["absent"], rows["Ana"]["attendanceRate"]) == (
        5,
        0,
        100.0,
    )
    assert (rows["=1+1 Bia"]["attendanceRate"], rows["=1+1 Bia"]["atRisk"]) == (60.0, True)
    assert (rows["Caio"]["attendanceRate"], rows["Caio"]["atRisk"]) == (75.0, False)
    assert rows["Caio"]["className"] == "6º Ano B"


async def test_period_filter(api: AsyncClient, seed: Seed) -> None:
    await _world(api, seed)

    response = await api.get(
        f"{REPORTS}/students",
        params={"from": "2026-11-19", "to": "2026-11-23"},
        headers=seed.headers,
    )

    rows = {r["fullName"]: (r["present"], r["absent"]) for r in response.json()["items"]}
    assert rows == {"Ana": (2, 0), "=1+1 Bia": (1, 1), "Caio": (1, 0)}


async def test_summary_and_by_class(api: AsyncClient, seed: Seed) -> None:
    world = await _world(api, seed)
    await api.post(
        f"/api/v1/school-years/{world.year['id']}/calendar-days",
        json={"day": "2026-11-20", "kind": "holiday"},
        headers=seed.headers,
    )

    summary = (await api.get(f"{REPORTS}/summary", params=PERIOD, headers=seed.headers)).json()
    by_class = (await api.get(f"{REPORTS}/by-class", params=PERIOD, headers=seed.headers)).json()

    # November 2026 has 21 weekdays; the 20th is a holiday.
    assert summary["schoolDays"] == 20
    assert (summary["lessons"], summary["students"]) == (9, 3)
    assert (summary["present"], summary["absent"]) == (11, 3)
    assert summary["attendanceRate"] == round(11 / 14 * 100, 1)
    assert summary["atRiskStudents"] == 1
    assert summary["minAttendanceRate"] == 75.0
    assert [
        (c["className"], c["lessons"], c["students"], c["atRiskStudents"])
        for c in by_class["items"]
    ] == [
        ("5º Ano A", 5, 2, 1),
        ("6º Ano B", 4, 1, 0),
    ]


async def test_low_attendance(api: AsyncClient, seed: Seed) -> None:
    await _world(api, seed)

    response = await api.get(f"{REPORTS}/low-attendance", params=PERIOD, headers=seed.headers)

    assert [r["fullName"] for r in response.json()["items"]] == ["=1+1 Bia"]


async def test_teacher_report_is_scoped(api: AsyncClient, seed: Seed) -> None:
    world = await _world(api, seed)

    own = await api.get(f"{REPORTS}/students", params=PERIOD, headers=world.teacher_a)
    other = await api.get(
        f"{REPORTS}/students",
        params={**PERIOD, "classId": world.class_b["id"]},
        headers=world.teacher_a,
    )

    assert {r["className"] for r in own.json()["items"]} == {"5º Ano A"}
    assert other.status_code == 404


async def test_invalid_period(api: AsyncClient, seed: Seed) -> None:
    inverted = await api.get(
        f"{REPORTS}/summary",
        params={"from": "2026-11-30", "to": "2026-11-01"},
        headers=seed.headers,
    )
    too_long = await api.get(
        f"{REPORTS}/summary",
        params={"from": "2025-01-01", "to": "2026-11-30"},
        headers=seed.headers,
    )
    missing = await api.get(f"{REPORTS}/summary", headers=seed.headers)

    assert inverted.json()["code"] == "invalid_date_range"
    assert too_long.json()["code"] == "date_range_too_long"
    assert inverted.status_code == too_long.status_code == missing.status_code == 422


async def test_csv_export(api: AsyncClient, db_session: AsyncSession, seed: Seed) -> None:
    await _world(api, seed)

    response = await api.get(
        f"{REPORTS}/export", params={**PERIOD, "format": "csv"}, headers=seed.headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="frequencia_2026-11-01_2026-11-30.csv"'
    )
    assert response.content.startswith("﻿".encode())
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
    assert rows[0][:2] == ["Matrícula", "Aluno"]
    by_name = {r[1]: r for r in rows[1:]}
    # Formula injection is neutralized; decimals use a comma.
    assert "'=1+1 Bia" in by_name
    assert by_name["'=1+1 Bia"][6:] == ["60,0", "Abaixo de 75%"]
    assert by_name["Ana"][3:7] == ["5", "0", "5", "100,0"]

    exported = await db_session.scalar(
        select(AuditLog).where(AuditLog.action == "reports.exported")
    )
    assert exported is not None
    assert exported.details["format"] == "csv"


async def test_xlsx_export(api: AsyncClient, seed: Seed) -> None:
    await _world(api, seed)

    response = await api.get(f"{REPORTS}/export", params=PERIOD, headers=seed.headers)

    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as workbook:
        index = workbook.read("xl/workbook.xml").decode()
        strings = workbook.read("xl/sharedStrings.xml").decode()
    for sheet in ("Resumo", "Por aluno", "Por turma", "Aulas", "Registros"):
        assert f'name="{sheet}"' in index
    assert "Aula 1" in strings  # teacher notes travel with the lessons
    assert "=1+1 Bia" in strings  # stored as text, never as a formula
