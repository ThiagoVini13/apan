"""Pydantic schemas for the classes module."""

from typing import Optional

from app.core.schemas import ApiModel
from app.core.schemas import Shift


class SubjectOut(ApiModel):
    id: str
    code: str
    name: str


class SchoolClassOut(ApiModel):
    id: str
    name: str
    grade: str
    section: str
    shift: Shift
    year: int
    student_count: int = 0


class SchoolClassListOut(ApiModel):
    items: list[SchoolClassOut]
    total: int
