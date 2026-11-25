from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from apan.core.schemas import ApiInput, ApiModel

ClassName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Grade = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
Room = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
Capacity = Annotated[int, Field(ge=1, le=500)]


class Shift(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class SchoolClassRead(ApiModel):
    id: UUID
    school_year_id: UUID
    name: str
    grade: str
    shift: Shift
    room: str | None
    capacity: int | None
    is_active: bool
    student_count: int = 0


class SchoolClassCreate(ApiInput):
    school_year_id: UUID
    name: ClassName
    grade: Grade
    shift: Shift
    room: Room | None = None
    capacity: Capacity | None = None


class SchoolClassUpdate(ApiInput):
    name: ClassName | None = None
    grade: Grade | None = None
    shift: Shift | None = None
    room: Room | None = None
    capacity: Capacity | None = None


class ClassFilters(ApiModel):
    school_year_id: UUID | None = None
    shift: Shift | None = None
    is_active: bool | None = None
    q: str | None = None


class SubjectTeacherRead(ApiModel):
    subject_id: UUID
    subject_name: str
    subject_code: str
    teacher_id: UUID
    teacher_name: str


class SubjectTeacherAssignment(ApiInput):
    subject_id: UUID
    teacher_id: UUID


class SubjectTeachersReplace(ApiInput):
    items: Annotated[list[SubjectTeacherAssignment], Field(max_length=50)]


class ClassInfo(ApiModel):
    """What other modules need to know about a class."""

    id: UUID
    school_year_id: UUID
    name: str
    is_active: bool
    capacity: int | None
