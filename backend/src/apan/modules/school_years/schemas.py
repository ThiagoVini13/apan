from datetime import date
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

from apan.core.schemas import ApiInput, ApiModel

ShortName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class CalendarDayKind(StrEnum):
    HOLIDAY = "holiday"
    RECESS = "recess"
    NON_SCHOOL_DAY = "non_school_day"
    EXTRA_SCHOOL_DAY = "extra_school_day"


class SchoolYearRead(ApiModel):
    id: UUID
    name: str
    starts_on: date
    ends_on: date
    is_current: bool


class SchoolYearCreate(ApiInput):
    name: ShortName
    starts_on: date
    ends_on: date
    is_current: bool = False


class SchoolYearUpdate(ApiInput):
    name: ShortName | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    is_current: bool | None = None


class TermRead(ApiModel):
    id: UUID
    school_year_id: UUID
    name: str
    starts_on: date
    ends_on: date


class TermCreate(ApiInput):
    name: ShortName
    starts_on: date
    ends_on: date


class CalendarDayRead(ApiModel):
    id: UUID
    school_year_id: UUID
    day: date
    kind: CalendarDayKind
    description: str | None


class CalendarDayCreate(ApiInput):
    day: date
    kind: CalendarDayKind
    description: Description | None = None
