from datetime import date, datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from apan.core.schemas import ApiInput, ApiModel

FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


class Relationship(StrEnum):
    MOTHER = "mother"
    FATHER = "father"
    GRANDPARENT = "grandparent"
    SIBLING = "sibling"
    UNCLE_AUNT = "uncle_aunt"
    LEGAL_GUARDIAN = "legal_guardian"
    OTHER = "other"


class GuardianRead(ApiModel):
    id: UUID
    full_name: str
    phone: str
    relationship: Relationship
    is_primary: bool


class GuardianCreate(ApiInput):
    full_name: FullName
    phone: Phone
    relationship: Relationship
    is_primary: bool = False


class GuardianUpdate(ApiInput):
    full_name: FullName | None = None
    phone: Phone | None = None
    relationship: Relationship | None = None
    is_primary: bool | None = None


class StudentRead(ApiModel):
    id: UUID
    enrollment_number: str
    full_name: str
    birth_date: date
    archived_at: datetime | None
    current_class_id: UUID | None = None
    current_enrollment_id: UUID | None = None


class StudentDetail(StudentRead):
    guardians: list[GuardianRead]


class StudentCreate(ApiInput):
    full_name: FullName
    birth_date: date
    # Required for teachers (one of their classes); optional for admins.
    class_id: UUID | None = None
    enrolled_on: date | None = None
    guardians: Annotated[list[GuardianCreate], Field(default_factory=list, max_length=5)]


class StudentUpdate(ApiInput):
    full_name: FullName | None = None
    birth_date: date | None = None


class StudentFilters(ApiModel):
    q: str | None = None
    class_id: UUID | None = None
    include_archived: bool = False
