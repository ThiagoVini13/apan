import uuid
from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apan.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RollCall(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One lesson: a class, a subject and a date, with the teacher's notes."""

    __tablename__ = "roll_calls"

    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("school_classes.id"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    lesson_date: Mapped[date]
    taken_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("class_id", "subject_id", "lesson_date"),
        CheckConstraint("char_length(notes) <= 1000", name="notes_length"),
        Index("ix_roll_calls_lesson_date", "lesson_date"),
        Index("ix_roll_calls_subject_id", "subject_id"),
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    roll_call_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roll_calls.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(10))

    __table_args__ = (
        CheckConstraint("status IN ('present', 'absent')", name="status_valid"),
        Index("ix_attendance_records_student_id", "student_id"),
    )
