"""Role x endpoint matrix for the registries.

The teacher is assigned to ``own`` class; ``other`` class is outside the scope.
Expected statuses are (anonymous, teacher, admin).
"""

from dataclasses import dataclass
from typing import Any

import pytest
from httpx import AsyncClient

from tests.factories.registries import DEFAULT_GUARDIAN, Seed


@dataclass
class World:
    year: dict[str, Any]
    subject: dict[str, Any]
    own: dict[str, Any]
    other: dict[str, Any]
    own_student: dict[str, Any]
    other_student: dict[str, Any]
    teacher: dict[str, str]


async def _world(seed: Seed) -> World:
    year = await seed.year()
    subject = await seed.subject()
    own = await seed.school_class(year["id"], name="Própria")
    other = await seed.school_class(year["id"], name="Alheia")
    _, teacher = await seed.teacher_in_class(own["id"], subject["id"])
    return World(
        year=year,
        subject=subject,
        own=own,
        other=other,
        own_student=await seed.student(own["id"]),
        other_student=await seed.student(other["id"]),
        teacher=teacher,
    )


def _new_student(w: World, class_key: str) -> dict[str, Any]:
    return {
        "fullName": "Novo",
        "birthDate": "2016-01-01",
        "classId": getattr(w, class_key)["id"],
        "guardians": [DEFAULT_GUARDIAN],
    }


# name, method, path (format with world), body, expected (anon, teacher, admin)
CASES: list[tuple[str, str, str, Any, tuple[int, int, int]]] = [
    ("list years", "GET", "/school-years", None, (401, 200, 200)),
    (
        "create year",
        "POST",
        "/school-years",
        {"name": "X", "startsOn": "2030-02-01", "endsOn": "2030-12-01"},
        (401, 403, 201),
    ),
    ("update year", "PATCH", "/school-years/{year[id]}", {"name": "Y"}, (401, 403, 200)),
    (
        "add term",
        "POST",
        "/school-years/{year[id]}/terms",
        {"name": "1º", "startsOn": "2026-02-01", "endsOn": "2026-04-30"},
        (401, 403, 201),
    ),
    (
        "add calendar day",
        "POST",
        "/school-years/{year[id]}/calendar-days",
        {"day": "2026-09-07", "kind": "holiday"},
        (401, 403, 201),
    ),
    ("list subjects", "GET", "/subjects", None, (401, 200, 200)),
    ("create subject", "POST", "/subjects", {"code": "NEW", "name": "Nova"}, (401, 403, 201)),
    ("update subject", "PATCH", "/subjects/{subject[id]}", {"name": "Z"}, (401, 403, 200)),
    ("list classes", "GET", "/classes", None, (401, 200, 200)),
    (
        "create class",
        "POST",
        "/classes",
        {"schoolYearId": "{year[id]}", "name": "N", "grade": "1", "shift": "evening"},
        (401, 403, 201),
    ),
    ("get own class", "GET", "/classes/{own[id]}", None, (401, 200, 200)),
    ("get other class", "GET", "/classes/{other[id]}", None, (401, 404, 200)),
    ("update class", "PATCH", "/classes/{own[id]}", {"room": "12"}, (401, 403, 200)),
    ("archive class", "POST", "/classes/{other[id]}/archive", None, (401, 403, 200)),
    ("own subject teachers", "GET", "/classes/{own[id]}/subject-teachers", None, (401, 200, 200)),
    (
        "other subject teachers",
        "GET",
        "/classes/{other[id]}/subject-teachers",
        None,
        (401, 404, 200),
    ),
    (
        "replace subject teachers",
        "PUT",
        "/classes/{other[id]}/subject-teachers",
        {"items": []},
        (401, 403, 200),
    ),
    ("own class students", "GET", "/classes/{own[id]}/students", None, (401, 200, 200)),
    ("other class students", "GET", "/classes/{other[id]}/students", None, (401, 404, 200)),
    ("list students", "GET", "/students", None, (401, 200, 200)),
    ("create student in own class", "POST", "/students", "own", (401, 201, 201)),
    ("create student in other class", "POST", "/students", "other", (401, 404, 201)),
    ("get own student", "GET", "/students/{own_student[id]}", None, (401, 200, 200)),
    ("get other student", "GET", "/students/{other_student[id]}", None, (401, 404, 200)),
    (
        "update own student",
        "PATCH",
        "/students/{own_student[id]}",
        {"fullName": "A"},
        (401, 200, 200),
    ),
    (
        "update other student",
        "PATCH",
        "/students/{other_student[id]}",
        {"fullName": "A"},
        (401, 404, 200),
    ),
    ("archive student", "POST", "/students/{own_student[id]}/archive", None, (401, 403, 200)),
    (
        "add guardian to own student",
        "POST",
        "/students/{own_student[id]}/guardians",
        DEFAULT_GUARDIAN,
        (401, 201, 201),
    ),
    (
        "add guardian to other student",
        "POST",
        "/students/{other_student[id]}/guardians",
        DEFAULT_GUARDIAN,
        (401, 404, 201),
    ),
    ("list enrollments", "GET", "/enrollments", None, (401, 200, 200)),
    (
        "get other enrollment",
        "GET",
        "/enrollments/{other_student[currentEnrollmentId]}",
        None,
        (401, 404, 200),
    ),
    (
        "cancel enrollment",
        "POST",
        "/enrollments/{own_student[currentEnrollmentId]}/cancel",
        {},
        (401, 403, 200),
    ),
]


def _format(value: Any, world: World) -> Any:
    if isinstance(value, str):
        return value.format(**vars(world))
    if isinstance(value, dict):
        return {k: _format(v, world) for k, v in value.items()}
    if isinstance(value, list):
        return [_format(v, world) for v in value]
    return value


@pytest.mark.parametrize(
    ("name", "method", "path", "body", "expected"), CASES, ids=[c[0] for c in CASES]
)
@pytest.mark.parametrize("caller", ["anonymous", "teacher", "admin"])
async def test_registries_authorization(
    api: AsyncClient,
    seed: Seed,
    name: str,
    method: str,
    path: str,
    body: Any,
    expected: tuple[int, int, int],
    caller: str,
) -> None:
    world = await _world(seed)
    headers = {"anonymous": {}, "teacher": world.teacher, "admin": seed.headers}[caller]
    payload = _new_student(world, body) if body in ("own", "other") else _format(body, world)

    response = await api.request(
        method, "/api/v1" + _format(path, world), json=payload, headers=headers
    )

    status = expected[["anonymous", "teacher", "admin"].index(caller)]
    assert response.status_code == status, f"{name} as {caller}: {response.text}"
