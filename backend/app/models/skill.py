"""
Skill and SkillCategory models.

Design decisions:
- Skills are a global catalog (not per-user). Each user references skills.
- Categories allow the trajectory engine to reason about skill clusters
  (e.g. "ML", "Cloud", "Soft Skills").
- normalized_name enables fuzzy/exact matching from raw user input.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, new_uuid


class SkillCategory(Base, TimestampMixin):
    """Top-level grouping of skills (e.g., Programming, Cloud, ML, Soft Skills)."""

    __tablename__ = "skill_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    skills: Mapped[list[Skill]] = relationship(
        "Skill", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SkillCategory name={self.name!r}>"


class Skill(Base, TimestampMixin):
    """
    Global skill catalog entry.

    normalized_name: lowercase, stripped name used for deduplication
                     and matching (e.g. "machine learning" → "machine_learning").
    """

    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skill_categories.id", ondelete="RESTRICT"), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    category: Mapped[SkillCategory] = relationship("SkillCategory", back_populates="skills")
    user_skills: Mapped[list[UserSkill]] = relationship(
        "UserSkill", back_populates="skill"
    )
    role_requirements: Mapped[list[RoleSkillRequirement]] = relationship(
        "RoleSkillRequirement", back_populates="skill"
    )

    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_skills_normalized_name"),
        Index("ix_skills_category_id", "category_id"),
        Index("ix_skills_normalized_name", "normalized_name"),
    )

    def __repr__(self) -> str:
        return f"<Skill name={self.name!r} category={self.category_id!r}>"


# Avoid circular imports
from app.models.profile import UserSkill  # noqa: E402, F401
from app.models.role import RoleSkillRequirement  # noqa: E402, F401
