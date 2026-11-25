"""roll calls and attendance records

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-25 00:58:13.219067+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roll_calls",
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("lesson_date", sa.Date(), nullable=False),
        sa.Column("taken_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("char_length(notes) <= 1000", name=op.f("ck_roll_calls_notes_length")),
        sa.ForeignKeyConstraint(
            ["class_id"], ["school_classes.id"], name=op.f("fk_roll_calls_class_id_school_classes")
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["subjects.id"], name=op.f("fk_roll_calls_subject_id_subjects")
        ),
        sa.ForeignKeyConstraint(
            ["taken_by_id"], ["users.id"], name=op.f("fk_roll_calls_taken_by_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"], ["users.id"], name=op.f("fk_roll_calls_updated_by_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roll_calls")),
        sa.UniqueConstraint(
            "class_id",
            "subject_id",
            "lesson_date",
            name=op.f("uq_roll_calls_class_id_subject_id_lesson_date"),
        ),
    )
    op.create_index("ix_roll_calls_lesson_date", "roll_calls", ["lesson_date"], unique=False)
    op.create_index("ix_roll_calls_subject_id", "roll_calls", ["subject_id"], unique=False)
    op.create_table(
        "attendance_records",
        sa.Column("roll_call_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.CheckConstraint(
            "status IN ('present', 'absent')", name=op.f("ck_attendance_records_status_valid")
        ),
        sa.ForeignKeyConstraint(
            ["roll_call_id"],
            ["roll_calls.id"],
            name=op.f("fk_attendance_records_roll_call_id_roll_calls"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("fk_attendance_records_student_id_students")
        ),
        sa.PrimaryKeyConstraint("roll_call_id", "student_id", name=op.f("pk_attendance_records")),
    )
    op.create_index(
        "ix_attendance_records_student_id", "attendance_records", ["student_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_records_student_id", table_name="attendance_records")
    op.drop_table("attendance_records")
    op.drop_index("ix_roll_calls_subject_id", table_name="roll_calls")
    op.drop_index("ix_roll_calls_lesson_date", table_name="roll_calls")
    op.drop_table("roll_calls")
