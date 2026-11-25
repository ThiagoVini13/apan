import uuid
from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from apan.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Enrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A student's stay in a class. ``school_year_id`` mirrors the class's year so the
    database can enforce one active enrollment per student per school year."""

    __tablename__ = "enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("school_classes.id"))
    school_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("school_years.id"))
    status: Mapped[str] = mapped_column(String(20))
    starts_on: Mapped[date]
    ends_on: Mapped[date | None]

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'transferred', 'cancelled', 'completed')", name="status_valid"
        ),
        CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="dates_ordered"),
        Index(
            "uq_enrollments_one_active_per_year",
            "student_id",
            "school_year_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_enrollments_class_id", "class_id"),
        Index("ix_enrollments_student_id", "student_id"),
    )
