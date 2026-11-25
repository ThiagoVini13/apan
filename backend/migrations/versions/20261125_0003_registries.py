"""registries: school years, terms, calendar, subjects, classes, students,
guardians and enrollments

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-25 00:38:14.754017+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ENROLLMENT_SEQUENCE = "student_enrollment_number_seq"


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(sa.Sequence(ENROLLMENT_SEQUENCE)))
    op.create_table(
        "school_years",
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.CheckConstraint("ends_on > starts_on", name=op.f("ck_school_years_dates_ordered")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_school_years")),
        sa.UniqueConstraint("name", name=op.f("uq_school_years_name")),
    )
    op.create_index(
        "uq_school_years_single_current",
        "school_years",
        ["is_current"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )
    op.create_table(
        "students",
        sa.Column("enrollment_number", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_students")),
        sa.UniqueConstraint("enrollment_number", name=op.f("uq_students_enrollment_number")),
    )
    op.create_table(
        "subjects",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subjects")),
        sa.UniqueConstraint("code", name=op.f("uq_subjects_code")),
    )
    op.create_table(
        "calendar_days",
        sa.Column("school_year_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
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
        sa.CheckConstraint(
            "kind IN ('holiday', 'recess', 'non_school_day', 'extra_school_day')",
            name=op.f("ck_calendar_days_kind_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["school_year_id"],
            ["school_years.id"],
            name=op.f("fk_calendar_days_school_year_id_school_years"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_calendar_days")),
        sa.UniqueConstraint(
            "school_year_id", "day", name=op.f("uq_calendar_days_school_year_id_day")
        ),
    )
    op.create_table(
        "guardians",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("relationship", sa.String(length=30), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.CheckConstraint(
            "relationship IN ('mother', 'father', 'grandparent', 'sibling', 'uncle_aunt', "
            "'legal_guardian', 'other')",
            name=op.f("ck_guardians_relationship_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_guardians_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_guardians")),
    )
    op.create_index("ix_guardians_student_id", "guardians", ["student_id"], unique=False)
    op.create_index(
        "uq_guardians_one_primary",
        "guardians",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    op.create_table(
        "school_classes",
        sa.Column("school_year_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("shift", sa.String(length=20), nullable=False),
        sa.Column("room", sa.String(length=50), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.CheckConstraint(
            "shift IN ('morning', 'afternoon', 'evening')",
            name=op.f("ck_school_classes_shift_valid"),
        ),
        sa.CheckConstraint(
            "capacity IS NULL OR capacity > 0", name=op.f("ck_school_classes_capacity_positive")
        ),
        sa.ForeignKeyConstraint(
            ["school_year_id"],
            ["school_years.id"],
            name=op.f("fk_school_classes_school_year_id_school_years"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_school_classes")),
        sa.UniqueConstraint(
            "school_year_id",
            "name",
            "shift",
            name=op.f("uq_school_classes_school_year_id_name_shift"),
        ),
    )
    op.create_index(
        "ix_school_classes_school_year_id", "school_classes", ["school_year_id"], unique=False
    )
    op.create_table(
        "terms",
        sa.Column("school_year_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
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
        sa.CheckConstraint("ends_on >= starts_on", name=op.f("ck_terms_dates_ordered")),
        sa.ForeignKeyConstraint(
            ["school_year_id"],
            ["school_years.id"],
            name=op.f("fk_terms_school_year_id_school_years"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_terms")),
        sa.UniqueConstraint("school_year_id", "name", name=op.f("uq_terms_school_year_id_name")),
    )
    op.create_table(
        "class_subject_teachers",
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["class_id"],
            ["school_classes.id"],
            name=op.f("fk_class_subject_teachers_class_id_school_classes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name=op.f("fk_class_subject_teachers_subject_id_subjects"),
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id"], ["users.id"], name=op.f("fk_class_subject_teachers_teacher_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_class_subject_teachers")),
        sa.UniqueConstraint(
            "class_id", "subject_id", name=op.f("uq_class_subject_teachers_class_id_subject_id")
        ),
    )
    op.create_index(
        "ix_class_subject_teachers_subject_id",
        "class_subject_teachers",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        "ix_class_subject_teachers_teacher_id",
        "class_subject_teachers",
        ["teacher_id"],
        unique=False,
    )
    op.create_table(
        "enrollments",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("school_year_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
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
        sa.CheckConstraint(
            "status IN ('active', 'transferred', 'cancelled', 'completed')",
            name=op.f("ck_enrollments_status_valid"),
        ),
        sa.CheckConstraint(
            "ends_on IS NULL OR ends_on >= starts_on", name=op.f("ck_enrollments_dates_ordered")
        ),
        sa.ForeignKeyConstraint(
            ["class_id"], ["school_classes.id"], name=op.f("fk_enrollments_class_id_school_classes")
        ),
        sa.ForeignKeyConstraint(
            ["school_year_id"],
            ["school_years.id"],
            name=op.f("fk_enrollments_school_year_id_school_years"),
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["students.id"], name=op.f("fk_enrollments_student_id_students")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enrollments")),
    )
    op.create_index("ix_enrollments_class_id", "enrollments", ["class_id"], unique=False)
    op.create_index("ix_enrollments_student_id", "enrollments", ["student_id"], unique=False)
    op.create_index(
        "uq_enrollments_one_active_per_year",
        "enrollments",
        ["student_id", "school_year_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_enrollments_one_active_per_year",
        table_name="enrollments",
        postgresql_where=sa.text("status = 'active'"),
    )
    op.drop_index("ix_enrollments_student_id", table_name="enrollments")
    op.drop_index("ix_enrollments_class_id", table_name="enrollments")
    op.drop_table("enrollments")
    op.drop_index("ix_class_subject_teachers_teacher_id", table_name="class_subject_teachers")
    op.drop_index("ix_class_subject_teachers_subject_id", table_name="class_subject_teachers")
    op.drop_table("class_subject_teachers")
    op.drop_table("terms")
    op.drop_index("ix_school_classes_school_year_id", table_name="school_classes")
    op.drop_table("school_classes")
    op.drop_index(
        "uq_guardians_one_primary", table_name="guardians", postgresql_where=sa.text("is_primary")
    )
    op.drop_index("ix_guardians_student_id", table_name="guardians")
    op.drop_table("guardians")
    op.drop_table("calendar_days")
    op.drop_table("subjects")
    op.drop_table("students")
    op.drop_index(
        "uq_school_years_single_current",
        table_name="school_years",
        postgresql_where=sa.text("is_current"),
    )
    op.drop_table("school_years")
    op.execute(sa.schema.DropSequence(sa.Sequence(ENROLLMENT_SEQUENCE)))
