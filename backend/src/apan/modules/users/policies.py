"""Who may do what with user accounts (pure functions)."""

from uuid import UUID

from apan.core.context import Actor
from apan.modules.users.schemas import UserUpdate

SELF_EDITABLE_FIELDS = frozenset({"full_name"})


def can_read(actor: Actor, user_id: UUID) -> bool:
    return actor.is_admin or actor.user_id == user_id


def can_update(actor: Actor, user_id: UUID, changes: UserUpdate) -> bool:
    if actor.is_admin:
        return True
    return actor.user_id == user_id and changes.model_fields_set <= SELF_EDITABLE_FIELDS
