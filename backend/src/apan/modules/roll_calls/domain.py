"""Pure roll call rules."""

from datetime import date, timedelta


def within_edit_window(lesson_date: date, today: date, window_days: int) -> bool:
    """Teachers may write roll calls from ``window_days`` ago up to today."""
    return today - timedelta(days=window_days) <= lesson_date <= today


def attendance_rate(present: int, absent: int) -> float | None:
    total = present + absent
    if total == 0:
        return None
    return round(present / total * 100, 1)
