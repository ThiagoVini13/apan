"""Who may do what with student records (pure functions).

- Admins: everything.
- Teachers: register students into their own classes and read/edit the students
  (and guardians) currently enrolled in those classes. Archiving and enrollment
  changes stay with admins.
"""

from apan.core.context import Actor


def requires_class_on_create(actor: Actor) -> bool:
    return not actor.is_admin


def can_see_archived(actor: Actor) -> bool:
    return actor.is_admin
