"""Role x endpoint matrix for roll calls, reports and the dashboard.

The teacher teaches ``subject`` in ``own``; ``other`` belongs to someone else.
Expected statuses are (anonymous, teacher, admin).
"""

from typing import Any

import pytest
from httpx import AsyncClient

from tests.factories.registries import Seed

MONDAY = "2026-11-23"
PERIOD = "from=2026-11-01&to=2026-11-30"


async def _world(api: AsyncClient, seed: Seed) -> dict[str, Any]:
    year = await seed.year()
    subject = await seed.subject()
    own = await seed.school_class(year["id"], name="Própria")
    other = await seed.school_class(year["id"], name="Alheia")
    _, teacher = await seed.teacher_in_class(own["id"], subject["id"])
    await seed.teacher_in_class(other["id"], subject["id"])
    own_student = await seed.student(own["id"], enrolled_on="2026-03-02")
    other_student = await seed.student(other["id"], enrolled_on="2026-03-02")
    other_roll_call = await api.put(
        "/api/v1/roll-calls",
        json={
            "classId": other["id"],
            "subjectId": subject["id"],
            "lessonDate": MONDAY,
            "attendances": [{"studentId": other_student["id"], "status": "present"}],
        },
        headers=seed.headers,
    )
    return {
        "subject": subject,
        "own": own,
        "other": other,
        "own_student": own_student,
        "other_roll_call": other_roll_call.json(),
        "teacher": teacher,
    }


def _roll_call(w: dict[str, Any], class_key: str) -> dict[str, Any]:
    students = [w["own_student"]] if class_key == "own" else []
    return {
        "classId": w[class_key]["id"],
        "subjectId": w["subject"]["id"],
        "lessonDate": MONDAY,
        "attendances": [{"studentId": s["id"], "status": "present"} for s in students],
    }


CASES: list[tuple[str, str, str, str | None, tuple[int, int, int]]] = [
    (
        "own sheet",
        "GET",
        "/roll-calls/sheet?classId={own[id]}&subjectId={subject[id]}&date=" + MONDAY,
        None,
        (401, 200, 200),
    ),
    (
        "other sheet",
        "GET",
        "/roll-calls/sheet?classId={other[id]}&subjectId={subject[id]}&date=" + MONDAY,
        None,
        (401, 404, 200),
    ),
    ("upsert own", "PUT", "/roll-calls", "own", (401, 200, 200)),
    ("upsert other", "PUT", "/roll-calls", "other", (401, 404, 422)),
    ("get other roll call", "GET", "/roll-calls/{other_roll_call[id]}", None, (401, 404, 200)),
    ("list roll calls", "GET", "/roll-calls", None, (401, 200, 200)),
    ("report summary", "GET", "/reports/attendance/summary?" + PERIOD, None, (401, 200, 200)),
    (
        "report other class",
        "GET",
        "/reports/attendance/students?" + PERIOD + "&classId={other[id]}",
        None,
        (401, 404, 200),
    ),
    ("export", "GET", "/reports/attendance/export?format=csv&" + PERIOD, None, (401, 200, 200)),
    ("dashboard", "GET", "/dashboard/today", None, (401, 200, 200)),
]


@pytest.mark.parametrize(
    ("name", "method", "path", "body", "expected"), CASES, ids=[c[0] for c in CASES]
)
@pytest.mark.parametrize("caller", ["anonymous", "teacher", "admin"])
async def test_attendance_authorization(
    api: AsyncClient,
    seed: Seed,
    name: str,
    method: str,
    path: str,
    body: str | None,
    expected: tuple[int, int, int],
    caller: str,
) -> None:
    world = await _world(api, seed)
    headers = {"anonymous": {}, "teacher": world["teacher"], "admin": seed.headers}[caller]
    payload = _roll_call(world, body) if body else None

    response = await api.request(
        method, "/api/v1" + path.format(**world), json=payload, headers=headers
    )

    status = expected[["anonymous", "teacher", "admin"].index(caller)]
    assert response.status_code == status, f"{name} as {caller}: {response.text}"
