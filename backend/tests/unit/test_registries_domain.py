from datetime import date

import pytest

from apan.modules.school_years.domain import overlaps, school_days
from apan.modules.students.domain import (
    age_on,
    birth_date_problem,
    enrollment_number,
    is_minor,
    normalize_phone,
)

TODAY = date(2026, 11, 24)


@pytest.mark.parametrize(
    ("birth", "expected"),
    [(date(2016, 11, 24), 10), (date(2016, 11, 25), 9), (date(2008, 2, 29), 18)],
)
def test_age_on(birth: date, expected: int) -> None:
    assert age_on(birth, TODAY) == expected


@pytest.mark.parametrize(
    ("birth", "problem"),
    [
        (date(2026, 12, 1), "date_in_future"),
        (date(2024, 1, 1), "student_too_young"),
        (date(2023, 11, 24), None),
        (date(1900, 1, 1), "invalid_birth_date"),
    ],
)
def test_birth_date_problem(birth: date, problem: str | None) -> None:
    assert birth_date_problem(birth, TODAY) == problem


def test_is_minor_until_eighteenth_birthday() -> None:
    assert is_minor(date(2008, 11, 25), TODAY) is True
    assert is_minor(date(2008, 11, 24), TODAY) is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("(92) 99123-4567", "92991234567"),
        ("+55 92 99123-4567", "92991234567"),
        ("92 3234-5678", "9232345678"),
        ("99123-4567", None),
        ("(92) 89123-4567", None),
        ("(02) 99123-4567", None),
        ("abc", None),
    ],
)
def test_normalize_phone(raw: str, expected: str | None) -> None:
    assert normalize_phone(raw) == expected


def test_enrollment_number_is_year_plus_sequence() -> None:
    assert enrollment_number(2026, 7) == "202600007"


def test_overlaps() -> None:
    assert overlaps(date(2026, 2, 1), date(2026, 4, 30), date(2026, 4, 30), date(2026, 7, 1))
    assert not overlaps(date(2026, 2, 1), date(2026, 4, 29), date(2026, 4, 30), date(2026, 7, 1))


def test_school_days_skip_weekends_and_holidays_and_add_extra_days() -> None:
    # Mon 2026-11-16 .. Sun 2026-11-22; Fri 20 is a holiday, Sat 21 an extra school day.
    days = school_days(
        date(2026, 11, 16),
        date(2026, 11, 22),
        [(date(2026, 11, 20), "holiday"), (date(2026, 11, 21), "extra_school_day")],
    )

    assert days == [
        date(2026, 11, 16),
        date(2026, 11, 17),
        date(2026, 11, 18),
        date(2026, 11, 19),
        date(2026, 11, 21),
    ]
