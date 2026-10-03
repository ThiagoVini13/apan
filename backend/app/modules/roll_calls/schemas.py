"""Pydantic schemas for the roll_calls module."""

from datetime import date, datetime
from typing import Optional

from app.core.schemas import ApiInput, ApiModel, AttendanceStatus


class AttendanceRecordOut(ApiModel):
    id: str
    student_id: str
    status: AttendanceStatus


class AttendanceRecordIn(ApiInput):
    student_id: str
    status: AttendanceStatus


class RollCallOut(ApiModel):
    id: str
    class_id: str
    subject_id: str
    lesson_date: date
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    attendances: list[AttendanceRecordOut] = []


class RollCallListOut(ApiModel):
    items: list[RollCallOut]
    total: int


class RollCallUpsertIn(ApiInput):
    class_id: str
    subject_id: str
    lesson_date: date
    notes: Optional[str] = None
    attendances: list[AttendanceRecordIn]
