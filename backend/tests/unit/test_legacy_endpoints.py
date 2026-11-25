"""Keeps the in-memory endpoints working until the roll calls PR replaces them."""

from httpx import AsyncClient


async def test_dashboard_today(client: AsyncClient) -> None:
    response = await client.get("/api/v1/dashboard/today")

    assert response.status_code == 200
    assert response.json()["totalClasses"] == 3


async def test_roll_calls_list(client: AsyncClient) -> None:
    response = await client.get("/api/v1/roll-calls")

    assert response.status_code == 200
