from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import EmailStr, StringConstraints

from apan.core.context import Role
from apan.core.schemas import ApiInput, ApiModel

FullName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class UserRead(ApiModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    created_at: datetime


class UserCreate(ApiInput):
    email: EmailStr
    full_name: FullName
    role: Role


class UserUpdate(ApiInput):
    """Admins may change every field; users may change only their own name."""

    email: EmailStr | None = None
    full_name: FullName | None = None
    role: Role | None = None


class UserFilters(ApiModel):
    q: str | None = None
    role: Role | None = None
    is_active: bool | None = None
