"""User accounts. Public interface: ``apan.modules.users.service``.

Keep this file free of router imports: the auth module imports the users
service, and the users router imports auth dependencies.
"""

from apan.modules.users.models import User

__all__ = ["User"]
