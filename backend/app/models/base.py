"""
Shared ORM base mixin — UUID primary key + timestamps.

All models inherit from TimestampMixin to avoid repeating these columns.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

# Re-export for convenience so models only need one import
from app.db.base import Base  # noqa: F401


class TimestampMixin:
    """
    Adds created_at / updated_at columns to every table that inherits it.
    Uses server-side defaults so the DB is the source of truth for timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def new_uuid() -> str:
    """Generate a new UUID4 string — used as default for PK columns."""
    return str(uuid.uuid4())
