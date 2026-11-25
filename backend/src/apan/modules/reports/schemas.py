from datetime import date
from enum import StrEnum
from uuid import UUID

from apan.core.schemas import ApiModel


class ExportFormat(StrEnum):
    XLSX = "xlsx"
    CSV = "csv"


class ReportParams(ApiModel):
    date_from: date
    date_to: date
    class_id: UUID | None = None
    subject_id: UUID | None = None
    student_id: UUID | None = None


class StudentReportRow(ApiModel):
    student_id: UUID
    full_name: str
    enrollment_number: str
    class_id: UUID
    class_name: str
    present: int
    absent: int
    total: int
    attendance_rate: float | None
    at_risk: bool


class ClassReportRow(ApiModel):
    class_id: UUID
    class_name: str
    lessons: int
    students: int
    present: int
    absent: int
    attendance_rate: float | None
    at_risk_students: int


class AttendanceSummary(ApiModel):
    date_from: date
    date_to: date
    school_days: int | None
    lessons: int
    students: int
    present: int
    absent: int
    attendance_rate: float | None
    at_risk_students: int
    min_attendance_rate: float
