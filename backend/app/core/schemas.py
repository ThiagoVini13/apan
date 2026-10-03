"""Core Pydantic base models and shared enums for the APAN API."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base response model: camelCase aliases, ORM-compatible."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ApiInput(ApiModel):
    """Base input model: forbids extra fields."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"


class Shift(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
