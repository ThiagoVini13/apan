"""Business logic for the students module."""

from typing import Any, Optional

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.store import store
from app.modules.students.schemas import (
    StudentCreateIn,
    StudentListOut,
    StudentOut,
    StudentUpdateIn,
)


def _compute_attendance_rate(student_id: str) -> Optional[float]:
    """Calculate attendance rate (%) for a student across all roll calls."""
    records = [
        r for r in store.attendance_records.values()
        if r["student_id"] == student_id
    ]
    if not records:
        return None
    present = sum(1 for r in records if r["status"] == "present")
    return round(present / len(records) * 100, 1)


def _to_out(student: dict[str, Any], with_rate: bool = False) -> StudentOut:
    data = dict(student)
    if with_rate:
        data["attendance_rate"] = _compute_attendance_rate(student["id"])
    return StudentOut.model_validate(data)


def list_students(
    q: Optional[str] = None,
    class_id: Optional[str] = None,
) -> StudentListOut:
    students = list(store.students.values())
    if q:
        q_lower = q.lower()
        students = [s for s in students if q_lower in s["full_name"].lower()]
    if class_id:
        students = [s for s in students if s["class_id"] == class_id]
    items = [_to_out(s) for s in students]
    return StudentListOut(items=items, total=len(items))


def get_student(student_id: str) -> StudentOut:
    student = store.students.get(student_id)
    if not student:
        raise NotFoundError("Student", student_id)
    return _to_out(student, with_rate=True)


def create_student(data: StudentCreateIn) -> StudentOut:
    # Validate class exists
    if data.class_id not in store.classes:
        raise ValidationError(f"Class '{data.class_id}' does not exist.")
    # Validate unique enrollment number
    for s in store.students.values():
        if s["enrollment_number"] == data.enrollment_number:
            raise ConflictError(
                f"Enrollment number '{data.enrollment_number}' is already in use."
            )
    student_id = store.next_id("stu")
    student: dict[str, Any] = {
        "id": student_id,
        **data.model_dump(),
    }
    store.students[student_id] = student
    return _to_out(student, with_rate=False)


def update_student(student_id: str, data: StudentUpdateIn) -> StudentOut:
    student = store.students.get(student_id)
    if not student:
        raise NotFoundError("Student", student_id)
    patch = data.model_dump(exclude_none=True)
    if "class_id" in patch and patch["class_id"] not in store.classes:
        raise ValidationError(f"Class '{patch['class_id']}' does not exist.")
    if "enrollment_number" in patch:
        for sid, s in store.students.items():
            if sid != student_id and s["enrollment_number"] == patch["enrollment_number"]:
                raise ConflictError(
                    f"Enrollment number '{patch['enrollment_number']}' is already in use."
                )
    student.update(patch)
    return _to_out(student, with_rate=True)
