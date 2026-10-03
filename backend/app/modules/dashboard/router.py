"""FastAPI router for the dashboard module."""

from datetime import date

from fastapi import APIRouter

from app.core.store import store
from app.modules.classes.schemas import SchoolClassOut
from app.modules.dashboard.schemas import DashboardTodayOut
from app.modules.students.schemas import StudentOut


router = APIRouter(prefix="/dashboard", tags=["dashboard"])

LOW_ATTENDANCE_THRESHOLD = 75.0


def _compute_attendance_rate(student_id: str) -> float:
    records = [
        ar for ar in store.attendance_records.values()
        if ar["student_id"] == student_id
    ]
    if not records:
        return 100.0  # no data -> assume full attendance
    present = sum(1 for ar in records if ar["status"] == "present")
    return round(present / len(records) * 100, 1)


def _student_count(class_id: str) -> int:
    return sum(1 for s in store.students.values() if s["class_id"] == class_id)


@router.get("/today", response_model=DashboardTodayOut)
def dashboard_today() -> DashboardTodayOut:
    """Return a snapshot for today's dashboard.

    If no roll calls exist for today, presence_rate reflects the most recent
    available data across all stored roll calls.
    """
    today = date.today()

    # Roll calls done today
    today_rcs = [rc for rc in store.roll_calls.values() if rc["lesson_date"] == today]
    roll_calls_completed = len(today_rcs)

    # Presence rate: prefer today's records; fall back to all records
    if today_rcs:
        today_rc_ids = {rc["id"] for rc in today_rcs}
        relevant_records = [
            ar for ar in store.attendance_records.values()
            if ar["roll_call_id"] in today_rc_ids
        ]
    else:
        relevant_records = list(store.attendance_records.values())

    if relevant_records:
        present_count = sum(1 for ar in relevant_records if ar["status"] == "present")
        presence_rate = round(present_count / len(relevant_records) * 100, 1)
    else:
        presence_rate = 0.0

    # Classes with no roll call today
    classes_with_rc_today = {rc["class_id"] for rc in today_rcs}
    pending_classes = [
        SchoolClassOut.model_validate(
            {**cls, "student_count": _student_count(cls["id"])}
        )
        for cls in store.classes.values()
        if cls["id"] not in classes_with_rc_today
    ]

    # Students with attendance rate below threshold
    low_attendance: list[StudentOut] = []
    for student in store.students.values():
        rate = _compute_attendance_rate(student["id"])
        if rate < LOW_ATTENDANCE_THRESHOLD:
            low_attendance.append(
                StudentOut.model_validate({**student, "attendance_rate": rate})
            )

    return DashboardTodayOut(
        total_students=len(store.students),
        total_classes=len(store.classes),
        roll_calls_completed=roll_calls_completed,
        presence_rate=presence_rate,
        classes_with_pending_roll_call=pending_classes,
        low_attendance_students=low_attendance,
    )
