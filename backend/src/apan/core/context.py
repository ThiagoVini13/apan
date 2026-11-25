"""Request-scoped identity types shared by every module."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    ADMIN = "admin"
    TEACHER = "teacher"


@dataclass(frozen=True, slots=True)
class ClientInfo:
    """Who is calling, for auditing and rate limiting."""

    ip: str | None
    user_agent: str | None

    @property
    def rate_limit_key(self) -> str:
        return self.ip or "unknown"


@dataclass(frozen=True, slots=True)
class Actor:
    """The authenticated user behind a request."""

    user_id: UUID
    role: Role
    session_id: UUID
    must_change_password: bool = False

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN


@dataclass(frozen=True, slots=True)
class AccessScope:
    """Classes an actor may reach. ``class_ids is None`` means unrestricted (admin)."""

    class_ids: frozenset[UUID] | None

    @property
    def unrestricted(self) -> bool:
        return self.class_ids is None

    def allows(self, class_id: UUID) -> bool:
        return self.class_ids is None or class_id in self.class_ids
