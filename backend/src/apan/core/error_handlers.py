"""Exception handlers that render every error as RFC 9457 problem details."""

from http import HTTPStatus
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from apan.core.database import violated_constraint
from apan.core.errors import AppError, FieldError

PROBLEM_JSON = "application/problem+json"

_logger = structlog.get_logger("apan.errors")

_HTTP_STATUS_CODES = {
    400: "bad_request",
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "validation_error",
    429: "rate_limited",
}


def _problem(
    request: Request,
    *,
    status: int,
    code: str,
    detail: str,
    title: str | None = None,
    field_errors: list[FieldError] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title or HTTPStatus(status).phrase,
        "status": status,
        "code": code,
        "detail": detail,
        "instance": request.url.path,
        "requestId": getattr(request.state, "request_id", None),
    }
    if field_errors:
        body["fieldErrors"] = [{"field": e.field, "code": e.code} for e in field_errors]
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)


async def _app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return _problem(
        request,
        status=exc.status,
        code=exc.code,
        detail=exc.detail,
        title=exc.title,
        field_errors=exc.field_errors,
        headers=exc.headers or None,
    )


def _field_name(location: tuple[int | str, ...]) -> str:
    parts = location[1:] if location and location[0] in {"body", "query", "path"} else location
    return ".".join(str(part) for part in parts) or "body"


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    field_errors = [
        FieldError(field=_field_name(tuple(error["loc"])), code=str(error["type"]))
        for error in exc.errors()
    ]
    return _problem(
        request,
        status=422,
        code="validation_error",
        detail="One or more fields are invalid.",
        title="Validation error",
        field_errors=field_errors,
    )


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    status = exc.status_code
    return _problem(
        request,
        status=status,
        code=_HTTP_STATUS_CODES.get(status, "http_error"),
        detail=exc.detail if isinstance(exc.detail, str) else HTTPStatus(status).phrase,
        headers=dict(exc.headers) if exc.headers else None,
    )


async def _integrity_error(request: Request, exc: Exception) -> JSONResponse:
    """Safety net for races that slip past the service checks."""
    assert isinstance(exc, IntegrityError)
    _logger.warning("integrity_error", constraint=violated_constraint(exc))
    return _problem(
        request,
        status=409,
        code="conflict",
        detail="The request conflicts with existing data.",
    )


async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    _logger.exception("unhandled_error", exc_type=type(exc).__name__)
    return _problem(
        request,
        status=500,
        code="internal_error",
        detail="An unexpected error occurred.",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(IntegrityError, _integrity_error)
    app.add_exception_handler(Exception, _unhandled_error)
