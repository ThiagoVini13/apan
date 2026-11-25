"""Pure date rules for the school calendar."""

from collections.abc import Iterable
from datetime import date, timedelta

WEEKEND = frozenset({5, 6})  # Saturday, Sunday
NON_SCHOOL_KINDS = frozenset({"holiday", "recess", "non_school_day"})
EXTRA_SCHOOL_KIND = "extra_school_day"


def overlaps(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return a_start <= b_end and b_start <= a_end


def within(start: date, end: date, outer_start: date, outer_end: date) -> bool:
    return outer_start <= start and end <= outer_end


def school_days(start: date, end: date, special_days: Iterable[tuple[date, str]]) -> list[date]:
    """Weekdays in [start, end] minus holidays/recess, plus extra school days."""
    special = dict(special_days)
    days: list[date] = []
    current = start
    while current <= end:
        kind = special.get(current)
        if kind == EXTRA_SCHOOL_KIND or (
            current.weekday() not in WEEKEND and kind not in NON_SCHOOL_KINDS
        ):
            days.append(current)
        current += timedelta(days=1)
    return days
