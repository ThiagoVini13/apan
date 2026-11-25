"""Pure authentication rules: password policy and token lifetimes."""

from datetime import datetime, timedelta
from enum import StrEnum

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128
MIN_DISTINCT_CHARACTERS = 4

# Frequent passwords with at least 10 characters (shorter ones fail on length).
COMMON_PASSWORDS = frozenset(
    {
        "0000000000",
        "0123456789",
        "0987654321",
        "1111111111",
        "1234567890",
        "123456789a",
        "1234567890a",
        "12345678910",
        "123123123123",
        "1q2w3e4r5t",
        "1q2w3e4r5t6y",
        "a123456789",
        "aaaaaaaaaa",
        "abc1234567",
        "abcdefghij",
        "admin12345",
        "administrator",
        "apan123456",
        "apannorte",
        "apannorte123",
        "brasil123456",
        "iloveyou12",
        "mudar12345",
        "mudar123456",
        "password12",
        "password123",
        "password1234",
        "passw0rd123",
        "professor123",
        "professora123",
        "qwerty1234",
        "qwerty123456",
        "qwertyuiop",
        "senha12345",
        "senha123456",
        "senha@12345",
        "senha@123456",
        "trocar12345",
        "zaq12wsxcde",
    }
)


class PasswordProblem(StrEnum):
    TOO_SHORT = "password_too_short"
    TOO_LONG = "password_too_long"
    TOO_COMMON = "password_too_common"
    CONTAINS_EMAIL = "password_contains_email"


def password_problems(password: str, email: str | None = None) -> list[PasswordProblem]:
    problems: list[PasswordProblem] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(PasswordProblem.TOO_SHORT)
    if len(password) > MAX_PASSWORD_LENGTH:
        problems.append(PasswordProblem.TOO_LONG)

    lowered = password.lower()
    if lowered in COMMON_PASSWORDS or len(set(lowered)) < MIN_DISTINCT_CHARACTERS:
        problems.append(PasswordProblem.TOO_COMMON)
    if email:
        local_part = email.split("@", 1)[0].lower()
        if lowered == email.lower() or (len(local_part) >= 4 and local_part in lowered):
            problems.append(PasswordProblem.CONTAINS_EMAIL)
    return problems


class ResetPurpose(StrEnum):
    RESET = "reset"
    INVITE = "invite"


def refresh_expiry(now: datetime, family_expires_at: datetime, ttl_days: int) -> datetime:
    """Sliding expiry, never past the family's absolute limit."""
    return min(now + timedelta(days=ttl_days), family_expires_at)
