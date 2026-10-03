"""
In-memory data store for the APAN MVP.

This module holds all simulated data for the application. It acts as a
singleton: import `store` to access and mutate the shared in-memory state.
Fixed UUIDs are used throughout to simplify manual testing.
"""

from datetime import date, datetime, timezone
from typing import Any

from app.core.schemas import AttendanceStatus, Shift

# ---------------------------------------------------------------------------
# Internal data containers (plain dicts for maximum flexibility)
# ---------------------------------------------------------------------------

# Subject records  {id: dict}
SUBJECTS: dict[str, dict[str, Any]] = {
    "subj-math-0001": {
        "id": "subj-math-0001",
        "code": "MATH",
        "name": "Matemática",
    },
    "subj-port-0001": {
        "id": "subj-port-0001",
        "code": "PORT",
        "name": "Português",
    },
}

# SchoolClass records  {id: dict}
CLASSES: dict[str, dict[str, Any]] = {
    "cls-5a-0001": {
        "id": "cls-5a-0001",
        "name": "5º Ano A",
        "grade": "5",
        "section": "A",
        "shift": Shift.MORNING,
        "year": 2026,
    },
    "cls-6b-0001": {
        "id": "cls-6b-0001",
        "name": "6º Ano B",
        "grade": "6",
        "section": "B",
        "shift": Shift.AFTERNOON,
        "year": 2026,
    },
    "cls-7c-0001": {
        "id": "cls-7c-0001",
        "name": "7º Ano C",
        "grade": "7",
        "section": "C",
        "shift": Shift.MORNING,
        "year": 2026,
    },
}

# Student records  {id: dict}
STUDENTS: dict[str, dict[str, Any]] = {
    # --- 5º Ano A ---
    "stu-0001": {
        "id": "stu-0001",
        "full_name": "Alice Souza",
        "enrollment_number": "20260001",
        "class_id": "cls-5a-0001",
        "birth_date": date(2016, 3, 14),
        "is_active": True,
    },
    "stu-0002": {
        "id": "stu-0002",
        "full_name": "Bruno Martins",
        "enrollment_number": "20260002",
        "class_id": "cls-5a-0001",
        "birth_date": date(2016, 7, 22),
        "is_active": True,
    },
    "stu-0003": {
        "id": "stu-0003",
        "full_name": "Carla Ferreira",
        "enrollment_number": "20260003",
        "class_id": "cls-5a-0001",
        "birth_date": date(2016, 1, 5),
        "is_active": True,
    },
    "stu-0004": {
        "id": "stu-0004",
        "full_name": "Daniel Oliveira",
        "enrollment_number": "20260004",
        "class_id": "cls-5a-0001",
        "birth_date": date(2016, 9, 30),
        "is_active": True,
    },
    "stu-0005": {
        "id": "stu-0005",
        "full_name": "Eduarda Lima",
        "enrollment_number": "20260005",
        "class_id": "cls-5a-0001",
        "birth_date": date(2016, 11, 18),
        "is_active": True,
    },
    # --- 6º Ano B ---
    "stu-0006": {
        "id": "stu-0006",
        "full_name": "Felipe Costa",
        "enrollment_number": "20260006",
        "class_id": "cls-6b-0001",
        "birth_date": date(2015, 4, 2),
        "is_active": True,
    },
    "stu-0007": {
        "id": "stu-0007",
        "full_name": "Gabriela Nunes",
        "enrollment_number": "20260007",
        "class_id": "cls-6b-0001",
        "birth_date": date(2015, 8, 17),
        "is_active": True,
    },
    "stu-0008": {
        "id": "stu-0008",
        "full_name": "Henrique Alves",
        "enrollment_number": "20260008",
        "class_id": "cls-6b-0001",
        "birth_date": date(2015, 12, 9),
        "is_active": True,
    },
    "stu-0009": {
        "id": "stu-0009",
        "full_name": "Isabela Rocha",
        "enrollment_number": "20260009",
        "class_id": "cls-6b-0001",
        "birth_date": date(2015, 6, 25),
        "is_active": True,
    },
    "stu-0010": {
        "id": "stu-0010",
        "full_name": "João Pereira",
        "enrollment_number": "20260010",
        "class_id": "cls-6b-0001",
        "birth_date": date(2015, 2, 11),
        "is_active": True,
    },
    # --- 7º Ano C ---
    "stu-0011": {
        "id": "stu-0011",
        "full_name": "Karen Ramos",
        "enrollment_number": "20260011",
        "class_id": "cls-7c-0001",
        "birth_date": date(2014, 5, 7),
        "is_active": True,
    },
    "stu-0012": {
        "id": "stu-0012",
        "full_name": "Lucas Barbosa",
        "enrollment_number": "20260012",
        "class_id": "cls-7c-0001",
        "birth_date": date(2014, 10, 20),
        "is_active": True,
    },
    "stu-0013": {
        "id": "stu-0013",
        "full_name": "Mariana Carvalho",
        "enrollment_number": "20260013",
        "class_id": "cls-7c-0001",
        "birth_date": date(2014, 3, 15),
        "is_active": True,
    },
    "stu-0014": {
        "id": "stu-0014",
        "full_name": "Nicolas Gomes",
        "enrollment_number": "20260014",
        "class_id": "cls-7c-0001",
        "birth_date": date(2014, 8, 3),
        "is_active": True,
    },
    "stu-0015": {
        "id": "stu-0015",
        "full_name": "Olivia Santos",
        "enrollment_number": "20260015",
        "class_id": "cls-7c-0001",
        "birth_date": date(2014, 1, 28),
        "is_active": True,
    },
}

# RollCall records  {id: dict}
# Simulated dates: a few days in the past so dashboard shows recent data.
ROLL_CALLS: dict[str, dict[str, Any]] = {
    "rc-0001": {
        "id": "rc-0001",
        "class_id": "cls-5a-0001",
        "subject_id": "subj-math-0001",
        "lesson_date": date(2026, 9, 30),
        "notes": "Revisão de frações.",
        "created_at": datetime(2026, 9, 30, 8, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 9, 30, 8, 5, tzinfo=timezone.utc),
    },
    "rc-0002": {
        "id": "rc-0002",
        "class_id": "cls-6b-0001",
        "subject_id": "subj-port-0001",
        "lesson_date": date(2026, 9, 30),
        "notes": "Leitura e interpretação de texto.",
        "created_at": datetime(2026, 9, 30, 13, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 9, 30, 13, 10, tzinfo=timezone.utc),
    },
    "rc-0003": {
        "id": "rc-0003",
        "class_id": "cls-7c-0001",
        "subject_id": "subj-math-0001",
        "lesson_date": date(2026, 10, 1),
        "notes": "Equações de 1º grau.",
        "created_at": datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 1, 8, 3, tzinfo=timezone.utc),
    },
}

# AttendanceRecord records  {id: dict}
ATTENDANCE_RECORDS: dict[str, dict[str, Any]] = {
    # rc-0001 — 5º Ano A — all present except Daniel
    "ar-0001": {"id": "ar-0001", "roll_call_id": "rc-0001", "student_id": "stu-0001", "status": AttendanceStatus.PRESENT},
    "ar-0002": {"id": "ar-0002", "roll_call_id": "rc-0001", "student_id": "stu-0002", "status": AttendanceStatus.PRESENT},
    "ar-0003": {"id": "ar-0003", "roll_call_id": "rc-0001", "student_id": "stu-0003", "status": AttendanceStatus.PRESENT},
    "ar-0004": {"id": "ar-0004", "roll_call_id": "rc-0001", "student_id": "stu-0004", "status": AttendanceStatus.ABSENT},
    "ar-0005": {"id": "ar-0005", "roll_call_id": "rc-0001", "student_id": "stu-0005", "status": AttendanceStatus.PRESENT},
    # rc-0002 — 6º Ano B — Felipe and Henrique absent
    "ar-0006": {"id": "ar-0006", "roll_call_id": "rc-0002", "student_id": "stu-0006", "status": AttendanceStatus.ABSENT},
    "ar-0007": {"id": "ar-0007", "roll_call_id": "rc-0002", "student_id": "stu-0007", "status": AttendanceStatus.PRESENT},
    "ar-0008": {"id": "ar-0008", "roll_call_id": "rc-0002", "student_id": "stu-0008", "status": AttendanceStatus.ABSENT},
    "ar-0009": {"id": "ar-0009", "roll_call_id": "rc-0002", "student_id": "stu-0009", "status": AttendanceStatus.PRESENT},
    "ar-0010": {"id": "ar-0010", "roll_call_id": "rc-0002", "student_id": "stu-0010", "status": AttendanceStatus.PRESENT},
    # rc-0003 — 7º Ano C — Nicolas and Olivia absent
    "ar-0011": {"id": "ar-0011", "roll_call_id": "rc-0003", "student_id": "stu-0011", "status": AttendanceStatus.PRESENT},
    "ar-0012": {"id": "ar-0012", "roll_call_id": "rc-0003", "student_id": "stu-0012", "status": AttendanceStatus.PRESENT},
    "ar-0013": {"id": "ar-0013", "roll_call_id": "rc-0003", "student_id": "stu-0013", "status": AttendanceStatus.PRESENT},
    "ar-0014": {"id": "ar-0014", "roll_call_id": "rc-0003", "student_id": "stu-0014", "status": AttendanceStatus.ABSENT},
    "ar-0015": {"id": "ar-0015", "roll_call_id": "rc-0003", "student_id": "stu-0015", "status": AttendanceStatus.ABSENT},
}


class InMemoryStore:
    """Thin wrapper that exposes the shared in-memory collections."""

    subjects = SUBJECTS
    classes = CLASSES
    students = STUDENTS
    roll_calls = ROLL_CALLS
    attendance_records = ATTENDANCE_RECORDS

    # --- helpers ---

    def next_id(self, prefix: str) -> str:
        """Generate a simple sequential id with the given prefix."""
        import uuid
        return f"{prefix}-{uuid.uuid4().hex[:8]}"


store = InMemoryStore()
