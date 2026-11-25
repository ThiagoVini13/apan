from httpx import AsyncClient


async def test_ready_when_database_and_redis_are_reachable(
    integration_client: AsyncClient,
) -> None:
    response = await integration_client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
