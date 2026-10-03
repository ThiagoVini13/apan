"""Pydantic schemas for the students module."""

from datetime import date
from typing import Optional

from app.core.schemas import ApiInput, ApiModel


class StudentBase(ApiModel):
    full_name: str
    enrollment_number: str
    class_id: str
    birth_date: Optional[date] = None
    is_active: bool = True


class StudentOut(StudentBase):
    id: str
    attendance_rate: Optional[float] = None  # percentage 0-100, computed on detail


class StudentListOut(ApiModel):
    items: list[StudentOut]
    total: int


class StudentCreateIn(ApiInput):
    full_name: str
    enrollment_number: str
    class_id: str
    birth_date: Optional[date] = None
    is_active: bool = True


class StudentUpdateIn(ApiInput):
    full_name: Optional[str] = None
    enrollment_number: Optional[str] = None
    class_id: Optional[str] = None
    birth_date: Optional[date] = None
    is_active: Optional[bool] = None
