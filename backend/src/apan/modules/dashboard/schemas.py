"""Pydantic schemas for the dashboard module."""

from apan.core.schemas import ApiModel
from apan.modules.classes.schemas import SchoolClassOut
from apan.modules.students.schemas import StudentOut


class DashboardTodayOut(ApiModel):
    total_students: int
    total_classes: int
    roll_calls_completed: int
    presence_rate: float
    classes_with_pending_roll_call: list[SchoolClassOut]
    low_attendance_students: list[StudentOut]
