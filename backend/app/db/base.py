"""
SQLAlchemy declarative base shared across all ORM models.

Import this Base in every model file so Alembic autogenerate
can discover all tables.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""
    pass
