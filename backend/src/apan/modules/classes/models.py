import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from apan.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SchoolClass(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "school_classes"

    school_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("school_years.id"))
    name: Mapped[str] = mapped_column(String(50))
    grade: Mapped[str] = mapped_column(String(20))
    shift: Mapped[str] = mapped_column(String(20))
    room: Mapped[str | None] = mapped_column(String(50))
    capacity: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())

    __table_args__ = (
        UniqueConstraint("school_year_id", "name", "shift"),
        CheckConstraint("shift IN ('morning', 'afternoon', 'evening')", name="shift_valid"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="capacity_positive"),
        Index("ix_school_classes_school_year_id", "school_year_id"),
    )


class ClassSubjectTeacher(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Which teacher teaches which subject in a class; drives the teacher's access scope."""

    __tablename__ = "class_subject_teachers"

    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("school_classes.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id"))
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        UniqueConstraint("class_id", "subject_id"),
        Index("ix_class_subject_teachers_teacher_id", "teacher_id"),
        Index("ix_class_subject_teachers_subject_id", "subject_id"),
    )
