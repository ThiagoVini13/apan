"""Pydantic schemas for the students module."""

from datetime import date

from apan.core.schemas import ApiInput, ApiModel


class StudentBase(ApiModel):
    full_name: str
    enrollment_number: str
    class_id: str
    birth_date: date | None = None
    is_active: bool = True


class StudentOut(StudentBase):
    id: str
    attendance_rate: float | None = None  # percentage 0-100, computed on detail


class StudentListOut(ApiModel):
    items: list[StudentOut]
    total: int


class StudentCreateIn(ApiInput):
    full_name: str
    enrollment_number: str
    class_id: str
    birth_date: date | None = None
    is_active: bool = True


class StudentUpdateIn(ApiInput):
    full_name: str | None = None
    enrollment_number: str | None = None
    class_id: str | None = None
    birth_date: date | None = None
    is_active: bool | None = None
