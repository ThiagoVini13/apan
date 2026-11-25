import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Sequence, String, false, text
from sqlalchemy.orm import Mapped, mapped_column

from apan.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin

ENROLLMENT_NUMBER_SEQUENCE = Sequence("student_enrollment_number_seq", metadata=Base.metadata)


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Minimal personal data (LGPD): name, birth date and a school-issued number."""

    __tablename__ = "students"

    enrollment_number: Mapped[str] = mapped_column(String(20), unique=True)
    full_name: Mapped[str] = mapped_column(String(200))
    birth_date: Mapped[date]
    archived_at: Mapped[datetime | None]


class Guardian(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "guardians"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str] = mapped_column(String(20))
    relationship: Mapped[str] = mapped_column(String(30))
    is_primary: Mapped[bool] = mapped_column(default=False, server_default=false())

    __table_args__ = (
        CheckConstraint(
            "relationship IN ('mother', 'father', 'grandparent', 'sibling', 'uncle_aunt', "
            "'legal_guardian', 'other')",
            name="relationship_valid",
        ),
        Index("ix_guardians_student_id", "student_id"),
        Index(
            "uq_guardians_one_primary",
            "student_id",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
    )
