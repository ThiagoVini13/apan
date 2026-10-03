"""Business logic for the classes module."""

from app.core.errors import NotFoundError
from app.core.store import store
from app.modules.classes.schemas import SchoolClassListOut, SchoolClassOut
from app.modules.students.schemas import StudentListOut, StudentOut


def _student_count(class_id: str) -> int:
    return sum(1 for s in store.students.values() if s["class_id"] == class_id)


def _to_out(cls: dict) -> SchoolClassOut:
    return SchoolClassOut.model_validate(
        {**cls, "student_count": _student_count(cls["id"])}
    )


def list_classes() -> SchoolClassListOut:
    items = [_to_out(c) for c in store.classes.values()]
    return SchoolClassListOut(items=items, total=len(items))


def get_class(class_id: str) -> SchoolClassOut:
    cls = store.classes.get(class_id)
    if not cls:
        raise NotFoundError("Class", class_id)
    return _to_out(cls)


def get_class_students(class_id: str) -> StudentListOut:
    if class_id not in store.classes:
        raise NotFoundError("Class", class_id)
    students = [
        StudentOut.model_validate(s)
        for s in store.students.values()
        if s["class_id"] == class_id
    ]
    return StudentListOut(items=students, total=len(students))
