from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

from apan.core.schemas import ApiInput, ApiModel

SubjectName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SubjectCode = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_upper=True,
        min_length=1,
        max_length=20,
        pattern=r"^[A-Za-z0-9_-]+$",
    ),
]


class SubjectRead(ApiModel):
    id: UUID
    name: str
    code: str


class SubjectCreate(ApiInput):
    name: SubjectName
    code: SubjectCode


class SubjectUpdate(ApiInput):
    name: SubjectName | None = None
    code: SubjectCode | None = None
