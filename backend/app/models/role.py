"""
Role / Job Title models.

Design:
- Role is a global catalog of job titles (e.g. "Data Scientist").
- RoleSkillRequirement is the many-to-many between roles and skills,
  with importance_level (1-5) so the engine can prioritize gaps.
- RoleTransition models historically observed or curated transitions
  between roles, giving the graph its edge weights.
"""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, new_uuid


class Role(Base, TimestampMixin):
    """
    A career role / job title in the global catalog.

    seniority_level: 1=Junior, 2=Mid, 3=Senior, 4=Lead/Principal, 5=Executive
    """

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "Data", "Engineering"
    seniority_level: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False
    )  # 1-5
    avg_salary_inr: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_years_to_reach: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    skill_requirements: Mapped[list[RoleSkillRequirement]] = relationship(
        "RoleSkillRequirement", back_populates="role", cascade="all, delete-orphan"
    )
    transitions_from: Mapped[list[RoleTransition]] = relationship(
        "RoleTransition",
        foreign_keys="RoleTransition.from_role_id",
        back_populates="from_role",
        cascade="all, delete-orphan",
    )
    transitions_to: Mapped[list[RoleTransition]] = relationship(
        "RoleTransition",
        foreign_keys="RoleTransition.to_role_id",
        back_populates="to_role",
    )

    __table_args__ = (
        UniqueConstraint("normalized_title", name="uq_roles_normalized_title"),
        CheckConstraint("seniority_level BETWEEN 1 AND 5", name="ck_roles_seniority"),
        Index("ix_roles_domain", "domain"),
        Index("ix_roles_normalized_title", "normalized_title"),
    )

    def __repr__(self) -> str:
        return f"<Role title={self.title!r} seniority={self.seniority_level}>"


class RoleSkillRequirement(Base, TimestampMixin):
    """
    Many-to-many: which skills are required/desirable for a role.

    importance_level:
        5 = Core / Non-negotiable
        4 = Important
        3 = Valuable
        2 = Nice-to-have
        1 = Bonus
    is_mandatory: True means a hard requirement (blocks gap resolution).
    """

    __tablename__ = "role_skill_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    importance_level: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )  # 1-5
    required_proficiency: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )  # 1-5
    is_mandatory: Mapped[bool] = mapped_column(default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    role: Mapped[Role] = relationship("Role", back_populates="skill_requirements")
    skill: Mapped[Skill] = relationship("Skill", back_populates="role_requirements")

    __table_args__ = (
        UniqueConstraint("role_id", "skill_id", name="uq_role_skill"),
        CheckConstraint(
            "importance_level BETWEEN 1 AND 5", name="ck_role_skill_importance"
        ),
        CheckConstraint(
            "required_proficiency BETWEEN 1 AND 5",
            name="ck_role_skill_required_proficiency",
        ),
        Index("ix_role_skill_role_id", "role_id"),
        Index("ix_role_skill_skill_id", "skill_id"),
    )

    def __repr__(self) -> str:
        return f"<RoleSkillRequirement role={self.role_id!r} skill={self.skill_id!r} importance={self.importance_level}>"


class RoleTransition(Base, TimestampMixin):
    """
    Directed edge in the career graph: from_role → to_role.

    transition_weight: probability / frequency score [0.0–1.0].
    avg_transition_months: typical time to make this transition.
    """

    __tablename__ = "role_transitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    to_role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    transition_weight: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    avg_transition_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    from_role: Mapped[Role] = relationship(
        "Role", foreign_keys=[from_role_id], back_populates="transitions_from"
    )
    to_role: Mapped[Role] = relationship(
        "Role", foreign_keys=[to_role_id], back_populates="transitions_to"
    )

    __table_args__ = (
        UniqueConstraint("from_role_id", "to_role_id", name="uq_role_transition"),
        CheckConstraint(
            "from_role_id != to_role_id", name="ck_transition_no_self_loop"
        ),
        CheckConstraint(
            "transition_weight BETWEEN 0.0 AND 1.0", name="ck_transition_weight"
        ),
        Index("ix_role_transition_from", "from_role_id"),
        Index("ix_role_transition_to", "to_role_id"),
    )

    def __repr__(self) -> str:
        return f"<RoleTransition {self.from_role_id!r} → {self.to_role_id!r} w={self.transition_weight}>"


# Circular-import resolution
from app.models.skill import Skill  # noqa: E402, F401
