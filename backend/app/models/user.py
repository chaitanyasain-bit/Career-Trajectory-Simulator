"""
User model — authentication identity only.
Career-specific data lives in UserProfile to keep concerns separated.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, new_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    profile: Mapped[UserProfile | None] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_users_email", "email"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"


# Avoid circular import — import after class definition
from app.models.profile import UserProfile  # noqa: E402, F401
