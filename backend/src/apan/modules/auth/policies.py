"""Permissions exposed to the frontend so it can show or hide features.

The backend still checks roles and scope on every endpoint.
"""

from apan.core.context import Role

PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN: frozenset(
        {
            "users:manage",
            "school_years:manage",
            "subjects:manage",
            "classes:manage",
            "students:manage",
            "enrollments:manage",
            "roll_calls:write_any",
            "reports:read_all",
            "audit_logs:read",
        }
    ),
    Role.TEACHER: frozenset(
        {
            "students:manage_own_classes",
            "roll_calls:write_own",
            "reports:read_own",
        }
    ),
}


def permissions_for(role: Role) -> list[str]:
    return sorted(PERMISSIONS[role])
