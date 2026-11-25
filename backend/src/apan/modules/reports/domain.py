"""Pure report rules."""

from datetime import date

from apan.core.constants import MIN_ATTENDANCE_RATE

MAX_RANGE_DAYS = 400
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def is_at_risk(rate: float | None) -> bool:
    return rate is not None and rate < MIN_ATTENDANCE_RATE


def range_problem(start: date, end: date) -> str | None:
    if end < start:
        return "invalid_date_range"
    if (end - start).days > MAX_RANGE_DAYS:
        return "date_range_too_long"
    return None


def safe_cell(value: str) -> str:
    """Neutralizes spreadsheet formula injection (CSV/Excel) in user-provided text."""
    return f"'{value}" if value.startswith(_FORMULA_PREFIXES) else value


def format_rate(rate: float | None) -> str:
    """Percentage with a decimal comma, as Brazilian spreadsheets expect."""
    return "" if rate is None else f"{rate:.1f}".replace(".", ",")
