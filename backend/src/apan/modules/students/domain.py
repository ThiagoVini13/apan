"""Pure rules for students and guardians."""

import re
from datetime import date

MIN_ENROLLMENT_AGE = 3
ADULT_AGE = 18
MAX_AGE = 120

_NON_DIGITS = re.compile(r"\D")


def age_on(birth_date: date, on: date) -> int:
    years = on.year - birth_date.year
    if (on.month, on.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def is_minor(birth_date: date, on: date) -> bool:
    return age_on(birth_date, on) < ADULT_AGE


def birth_date_problem(birth_date: date, on: date) -> str | None:
    if birth_date > on:
        return "date_in_future"
    age = age_on(birth_date, on)
    if age < MIN_ENROLLMENT_AGE:
        return "student_too_young"
    if age > MAX_AGE:
        return "invalid_birth_date"
    return None


def normalize_phone(raw: str) -> str | None:
    """Brazilian phone with area code: 10 (landline) or 11 (mobile) digits.

    Accepts formatting and an optional +55 prefix; returns digits only or None.
    """
    digits = _NON_DIGITS.sub("", raw)
    if len(digits) in (12, 13) and digits.startswith("55"):
        digits = digits[2:]
    if len(digits) not in (10, 11) or digits[0] == "0":
        return None
    if len(digits) == 11 and digits[2] != "9":
        return None
    return digits


def enrollment_number(year: int, sequence_value: int) -> str:
    return f"{year}{sequence_value:05d}"
