from fastapi import FastAPI
from httpx import AsyncClient

from apan.core.errors import FieldError, NotFoundError, ValidationError


async def test_app_error_is_rendered_as_problem_details(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/boom")
    async def boom() -> None:
        raise NotFoundError("Student 42 is gone", code="student_not_found")

    response = await client.get("/boom")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == 404
    assert body["code"] == "student_not_found"
    assert body["instance"] == "/boom"
    assert body["requestId"] == response.headers["x-request-id"]


async def test_field_errors_are_listed(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/invalid")
    async def invalid() -> None:
        raise ValidationError(field_errors=[FieldError("birthDate", "date_in_future")])

    body = (await client.get("/invalid")).json()

    assert body["code"] == "validation_error"
    assert body["fieldErrors"] == [{"field": "birthDate", "code": "date_in_future"}]


async def test_request_validation_uses_camel_case_fields(app: FastAPI, client: AsyncClient) -> None:

    from apan.core.schemas import ApiInput

    class Payload(ApiInput):
        full_name: str
        enrollment_number: str

    @app.post("/validate")
    async def validate(body: Payload) -> None:
        return None

    response = await client.post("/validate", json={"fullName": "Ana", "unknown": 1})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    fields = {error["field"] for error in body["fieldErrors"]}
    assert fields == {"enrollmentNumber", "unknown"}


async def test_unknown_route_returns_not_found_problem(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_unhandled_error_hides_internals(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internal detail")

    response = await client.get("/crash")

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "secret" not in response.text
