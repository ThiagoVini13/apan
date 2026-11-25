from datetime import datetime

from sqlalchemy import CheckConstraint, String, false, true
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from apan.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    # NULL until an invited user defines a password.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    must_change_password: Mapped[bool] = mapped_column(default=False, server_default=false())
    failed_login_count: Mapped[int] = mapped_column(default=0, server_default="0")
    locked_until: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'teacher')", name="role_valid"),
        CheckConstraint("failed_login_count >= 0", name="failed_login_count_non_negative"),
    )
