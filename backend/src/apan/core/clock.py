from datetime import UTC, date, datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from apan.core.config import get_settings


@lru_cache
def _school_zone() -> ZoneInfo:
    return ZoneInfo(get_settings().school_timezone)


def now() -> datetime:
    return datetime.now(UTC)


def local_today() -> date:
    """Today in the school's time zone."""
    return datetime.now(_school_zone()).date()
