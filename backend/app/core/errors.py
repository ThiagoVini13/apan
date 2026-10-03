"""Application error classes used across all modules."""


class AppError(Exception):
    """Base application error."""

    code: str = "APP_ERROR"
    status_code: int = 500

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    code: str = "NOT_FOUND"
    status_code: int = 404

    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} with id '{id}' not found.")


class ValidationError(AppError):
    """Raised when business rule validation fails."""

    code: str = "VALIDATION_ERROR"
    status_code: int = 422

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class ConflictError(AppError):
    """Raised when a resource conflict occurs."""

    code: str = "CONFLICT"
    status_code: int = 409

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
