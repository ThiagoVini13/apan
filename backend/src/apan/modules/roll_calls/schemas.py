from datetime import date, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from apan.core.schemas import ApiInput, ApiModel

MAX_NOTES_LENGTH = 1000

Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=MAX_NOTES_LENGTH)]


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"


class AttendanceRead(ApiModel):
    student_id: UUID
    status: AttendanceStatus


class RollCallRead(ApiModel):
    id: UUID
    class_id: UUID
    subject_id: UUID
    lesson_date: date
    notes: str | None
    taken_by_id: UUID
    updated_by_id: UUID
    created_at: datetime
    updated_at: datetime
    present_count: int
    absent_count: int
    attendances: list[AttendanceRead]


class RollCallSummary(ApiModel):
    id: UUID
    class_id: UUID
    subject_id: UUID
    lesson_date: date
    notes: str | None
    present_count: int
    absent_count: int


class AttendanceIn(ApiInput):
    student_id: UUID
    status: AttendanceStatus


class RollCallUpsert(ApiInput):
    class_id: UUID
    subject_id: UUID
    lesson_date: date
    notes: Notes | None = None
    attendances: Annotated[list[AttendanceIn], Field(max_length=200)]


class RollCallFilters(ApiModel):
    class_id: UUID | None = None
    subject_id: UUID | None = None
    lesson_date: date | None = None
    date_from: date | None = None
    date_to: date | None = None


class SheetStudent(ApiModel):
    student_id: UUID
    full_name: str
    enrollment_number: str
    status: AttendanceStatus | None


class RollCallSheet(ApiModel):
    """Everything the roll call screen needs for one lesson."""

    class_id: UUID
    subject_id: UUID
    lesson_date: date
    roll_call_id: UUID | None
    notes: str | None
    is_school_day: bool
    editable: bool
    students: list[SheetStudent]


class AttendanceQuery(ApiModel):
    """Filters for attendance aggregations (used by reports and the dashboard)."""

    start: date
    end: date
    class_ids: frozenset[UUID] | None = None
    class_id: UUID | None = None
    subject_id: UUID | None = None
    student_id: UUID | None = None


class StudentTotals(ApiModel):
    student_id: UUID
    class_id: UUID
    present: int
    absent: int


class LessonRow(ApiModel):
    roll_call_id: UUID
    class_id: UUID
    subject_id: UUID
    lesson_date: date
    taken_by_id: UUID
    notes: str | None
    present: int
    absent: int


class RecordRow(ApiModel):
    lesson_date: date
    class_id: UUID
    subject_id: UUID
    student_id: UUID
    status: AttendanceStatus
