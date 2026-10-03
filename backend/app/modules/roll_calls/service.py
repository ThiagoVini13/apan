"""Business logic for the roll_calls module."""

from datetime import date, datetime, timezone
from typing import Any, Optional

from app.core.errors import NotFoundError, ValidationError
from app.core.store import store
from app.modules.roll_calls.schemas import (
    AttendanceRecordOut,
    RollCallListOut,
    RollCallOut,
    RollCallUpsertIn,
)


def _build_attendances(roll_call_id: str) -> list[AttendanceRecordOut]:
    return [
        AttendanceRecordOut.model_validate(ar)
        for ar in store.attendance_records.values()
        if ar["roll_call_id"] == roll_call_id
    ]


def _to_out(rc: dict[str, Any]) -> RollCallOut:
    return RollCallOut.model_validate(
        {**rc, "attendances": _build_attendances(rc["id"])}
    )


def list_roll_calls(
    class_id: Optional[str] = None,
    lesson_date: Optional[date] = None,
) -> RollCallListOut:
    roll_calls = list(store.roll_calls.values())
    if class_id:
        roll_calls = [rc for rc in roll_calls if rc["class_id"] == class_id]
    if lesson_date:
        roll_calls = [rc for rc in roll_calls if rc["lesson_date"] == lesson_date]
    items = [_to_out(rc) for rc in roll_calls]
    return RollCallListOut(items=items, total=len(items))


def get_roll_call(roll_call_id: str) -> RollCallOut:
    rc = store.roll_calls.get(roll_call_id)
    if not rc:
        raise NotFoundError("RollCall", roll_call_id)
    return _to_out(rc)


def upsert_roll_call(data: RollCallUpsertIn) -> RollCallOut:
    # Validate class exists
    cls = store.classes.get(data.class_id)
    if not cls:
        raise NotFoundError("Class", data.class_id)
    # Validate subject exists
    if data.subject_id not in store.subjects:
        raise NotFoundError("Subject", data.subject_id)

    # Ensure all students of the class are included
    class_student_ids = {
        sid for sid, s in store.students.items() if s["class_id"] == data.class_id
    }
    submitted_ids = {a.student_id for a in data.attendances}
    missing = class_student_ids - submitted_ids
    if missing:
        raise ValidationError(
            f"Missing attendance records for student(s): {', '.join(sorted(missing))}"
        )
    extra = submitted_ids - class_student_ids
    if extra:
        raise ValidationError(
            f"Student(s) not in class: {', '.join(sorted(extra))}"
        )

    now = datetime.now(tz=timezone.utc)

    # Find existing roll call for same class+subject+date (upsert)
    existing_rc: Optional[dict[str, Any]] = None
    for rc in store.roll_calls.values():
        if (
            rc["class_id"] == data.class_id
            and rc["subject_id"] == data.subject_id
            and rc["lesson_date"] == data.lesson_date
        ):
            existing_rc = rc
            break

    if existing_rc:
        roll_call_id = existing_rc["id"]
        existing_rc["notes"] = data.notes
        existing_rc["updated_at"] = now
        # Remove old attendance records
        to_delete = [
            k for k, ar in store.attendance_records.items()
            if ar["roll_call_id"] == roll_call_id
        ]
        for k in to_delete:
            del store.attendance_records[k]
    else:
        roll_call_id = store.next_id("rc")
        store.roll_calls[roll_call_id] = {
            "id": roll_call_id,
            "class_id": data.class_id,
            "subject_id": data.subject_id,
            "lesson_date": data.lesson_date,
            "notes": data.notes,
            "created_at": now,
            "updated_at": now,
        }

    # Insert new attendance records
    for att in data.attendances:
        ar_id = store.next_id("ar")
        store.attendance_records[ar_id] = {
            "id": ar_id,
            "roll_call_id": roll_call_id,
            "student_id": att.student_id,
            "status": att.status,
        }

    return _to_out(store.roll_calls[roll_call_id])
