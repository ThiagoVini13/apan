from typing import Annotated, Literal
from uuid import UUID

from pydantic import EmailStr, StringConstraints

from apan.core.context import Role
from apan.core.schemas import ApiInput, ApiModel
from apan.modules.auth.domain import MAX_PASSWORD_LENGTH

# Length is checked by the password policy (with stable codes); this only caps abuse.
Password = Annotated[str, StringConstraints(min_length=1, max_length=MAX_PASSWORD_LENGTH * 2)]
OpaqueToken = Annotated[str, StringConstraints(min_length=16, max_length=256)]


class LoginIn(ApiInput):
    email: EmailStr
    password: Password


class MeRead(ApiModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    must_change_password: bool
    permissions: list[str]


class TokenRead(ApiModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int
    user: MeRead


class PasswordChangeIn(ApiInput):
    current_password: Password
    new_password: Password


class PasswordForgotIn(ApiInput):
    email: EmailStr


class PasswordResetIn(ApiInput):
    token: OpaqueToken
    new_password: Password
