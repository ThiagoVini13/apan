from datetime import date
from enum import StrEnum
from uuid import UUID

from apan.core.schemas import ApiInput, ApiModel


class EnrollmentStatus(StrEnum):
    ACTIVE = "active"
    TRANSFERRED = "transferred"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class EnrollmentRead(ApiModel):
    id: UUID
    student_id: UUID
    class_id: UUID
    school_year_id: UUID
    status: EnrollmentStatus
    starts_on: date
    ends_on: date | None


class EnrollmentCreate(ApiInput):
    student_id: UUID
    class_id: UUID
    starts_on: date | None = None


class EnrollmentTransfer(ApiInput):
    class_id: UUID
    transfer_on: date | None = None


class EnrollmentCancel(ApiInput):
    ends_on: date | None = None


class EnrollmentFilters(ApiModel):
    student_id: UUID | None = None
    class_id: UUID | None = None
    school_year_id: UUID | None = None
    status: EnrollmentStatus | None = None
