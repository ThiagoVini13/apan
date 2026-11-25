"""Legacy dashboard schemas (in-memory data), replaced in the roll calls PR."""

from datetime import date

from apan.core.schemas import ApiModel, Shift


class SchoolClassOut(ApiModel):
    id: str
    name: str
    grade: str
    section: str
    shift: Shift
    year: int
    student_count: int = 0


class StudentOut(ApiModel):
    id: str
    full_name: str
    enrollment_number: str
    class_id: str
    birth_date: date | None = None
    is_active: bool = True
    attendance_rate: float | None = None


class DashboardTodayOut(ApiModel):
    total_students: int
    total_classes: int
    roll_calls_completed: int
    presence_rate: float
    classes_with_pending_roll_call: list[SchoolClassOut]
    low_attendance_students: list[StudentOut]
