from datetime import date

import pytest

from apan.modules.reports.domain import format_rate, is_at_risk, range_problem, safe_cell
from apan.modules.roll_calls.domain import attendance_rate, within_edit_window

TODAY = date(2026, 11, 24)


@pytest.mark.parametrize(
    ("lesson", "expected"),
    [
        (date(2026, 11, 24), True),
        (date(2026, 11, 17), True),
        (date(2026, 11, 16), False),
        (date(2026, 11, 25), False),
    ],
)
def test_edit_window(lesson: date, expected: bool) -> None:
    assert within_edit_window(lesson, TODAY, window_days=7) is expected


def test_attendance_rate() -> None:
    assert attendance_rate(3, 1) == 75.0
    assert attendance_rate(2, 1) == 66.7
    assert attendance_rate(0, 0) is None


def test_at_risk_is_strictly_below_75() -> None:
    assert is_at_risk(74.9) is True
    assert is_at_risk(75.0) is False
    assert is_at_risk(None) is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('=HYPERLINK("http://x")', '\'=HYPERLINK("http://x")'),
        ("+55 92", "'+55 92"),
        ("-1", "'-1"),
        ("@SUM(A1)", "'@SUM(A1)"),
        ("Ana Souza", "Ana Souza"),
    ],
)
def test_safe_cell(value: str, expected: str) -> None:
    assert safe_cell(value) == expected


def test_format_rate_uses_decimal_comma() -> None:
    assert format_rate(87.5) == "87,5"
    assert format_rate(None) == ""


def test_range_problem() -> None:
    assert range_problem(date(2026, 1, 1), date(2026, 12, 31)) is None
    assert range_problem(date(2026, 2, 1), date(2026, 1, 1)) == "invalid_date_range"
    assert range_problem(date(2025, 1, 1), date(2026, 12, 31)) == "date_range_too_long"
