"""Typed application errors.

Every error carries a stable ``code`` (English, snake_case) that the frontend
translates. ``detail`` is meant for developers only and never shown to users.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class FieldError:
    field: str
    code: str


class AppError(Exception):
    status: ClassVar[int] = 500
    title: ClassVar[str] = "Internal server error"
    default_code: ClassVar[str] = "internal_error"

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        field_errors: list[FieldError] | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.detail = detail or self.title
        self.field_errors = field_errors or []
        super().__init__(self.detail)


class BadRequestError(AppError):
    status = 400
    title = "Bad request"
    default_code = "bad_request"


class AuthenticationError(AppError):
    status = 401
    title = "Not authenticated"
    default_code = "not_authenticated"


class PermissionDeniedError(AppError):
    status = 403
    title = "Permission denied"
    default_code = "permission_denied"


class NotFoundError(AppError):
    status = 404
    title = "Resource not found"
    default_code = "not_found"


class ConflictError(AppError):
    status = 409
    title = "Conflict"
    default_code = "conflict"


class ValidationError(AppError):
    status = 422
    title = "Validation error"
    default_code = "validation_error"


class RateLimitError(AppError):
    status = 429
    title = "Too many requests"
    default_code = "rate_limited"


class ServiceUnavailableError(AppError):
    status = 503
    title = "Service unavailable"
    default_code = "service_unavailable"
