import uuid
from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, false, text
from sqlalchemy.orm import Mapped, mapped_column

from apan.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SchoolYear(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "school_years"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    starts_on: Mapped[date]
    ends_on: Mapped[date]
    is_current: Mapped[bool] = mapped_column(default=False, server_default=false())

    __table_args__ = (
        CheckConstraint("ends_on > starts_on", name="dates_ordered"),
        Index(
            "uq_school_years_single_current",
            "is_current",
            unique=True,
            postgresql_where=text("is_current"),
        ),
    )


class Term(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Bimestre/trimestre."""

    __tablename__ = "terms"

    school_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("school_years.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(50))
    starts_on: Mapped[date]
    ends_on: Mapped[date]

    __table_args__ = (
        UniqueConstraint("school_year_id", "name"),
        CheckConstraint("ends_on >= starts_on", name="dates_ordered"),
    )


class CalendarDay(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A day that differs from the regular Monday-to-Friday school calendar."""

    __tablename__ = "calendar_days"

    school_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("school_years.id", ondelete="CASCADE")
    )
    day: Mapped[date]
    kind: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(200))

    __table_args__ = (
        UniqueConstraint("school_year_id", "day"),
        CheckConstraint(
            "kind IN ('holiday', 'recess', 'non_school_day', 'extra_school_day')",
            name="kind_valid",
        ),
    )
