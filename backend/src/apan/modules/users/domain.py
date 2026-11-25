"""Pure rules for user accounts."""

from datetime import datetime, timedelta

MAX_LOCKOUT = timedelta(hours=24)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def lockout_duration(failed_count: int, max_attempts: int, base_minutes: int) -> timedelta | None:
    """Every ``max_attempts`` consecutive failures lock the account, doubling each time."""
    if failed_count < max_attempts or failed_count % max_attempts != 0:
        return None
    exponent = failed_count // max_attempts - 1
    return min(timedelta(minutes=base_minutes * 2**exponent), MAX_LOCKOUT)


def is_locked(locked_until: datetime | None, now: datetime) -> bool:
    return locked_until is not None and locked_until > now
