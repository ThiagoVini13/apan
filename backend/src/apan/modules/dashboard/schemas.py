from datetime import date
from uuid import UUID

from apan.core.schemas import ApiModel


class PendingRollCall(ApiModel):
    class_id: UUID
    class_name: str
    subject_id: UUID
    subject_name: str
    teacher_id: UUID
    teacher_name: str


class AtRiskStudent(ApiModel):
    student_id: UUID
    full_name: str
    class_id: UUID
    class_name: str
    attendance_rate: float


class DashboardToday(ApiModel):
    date: date
    school_year_id: UUID | None
    school_year_name: str | None
    is_school_day: bool
    total_classes: int
    total_students: int
    roll_calls_expected: int
    roll_calls_done: int
    presence_rate_today: float | None
    presence_rate_last_30_days: float | None
    pending_roll_calls: list[PendingRollCall]
    low_attendance_students: list[AtRiskStudent]
