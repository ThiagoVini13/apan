from httpx import AsyncClient


async def test_generates_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live")

    assert len(response.headers["x-request-id"]) == 32


async def test_propagates_valid_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live", headers={"X-Request-ID": "abc-123_def.456"})

    assert response.headers["x-request-id"] == "abc-123_def.456"


async def test_replaces_malformed_request_id(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/live", headers={"X-Request-ID": "bad id"})

    assert response.headers["x-request-id"] != "bad id"
    assert len(response.headers["x-request-id"]) == 32
