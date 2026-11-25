"""Keeps the in-memory endpoints working until each module moves to the database."""

from httpx import AsyncClient


async def test_students_list_includes_attendance_rate(client: AsyncClient) -> None:
    response = await client.get("/api/v1/students")

    assert response.status_code == 200
    assert all("attendanceRate" in student for student in response.json()["items"])


async def test_missing_student_has_stable_code(client: AsyncClient) -> None:
    response = await client.get("/api/v1/students/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == "student_not_found"


async def test_dashboard_today(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard/today")

    assert response.status_code == 200
    assert response.json()["totalClasses"] == 3
