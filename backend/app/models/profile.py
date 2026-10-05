"""
User career profile, user skills, education, and work experience models.

Design decisions:
- UserProfile is 1:1 with User (separate table for clean separation).
- UserSkill is the user-specific skill assertion with a proficiency level.
- Education and Experience are free-form but typed.
- proficiency_level: 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert
"""

from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, new_uuid


class UserProfile(Base, TimestampMixin):
    """
    Career-specific profile data for a user.

    current_role_id: FK → Role (the role the user holds right now).
    years_of_experience: total professional years (float for "2.5 years" etc.)
    bio: optional free-text self-description used for context.
    """

    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_role_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )
    years_of_experience: Mapped[float] = mapped_column(default=0.0, nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="profile")
    current_role: Mapped[Role | None] = relationship("Role")
    user_skills: Mapped[list[UserSkill]] = relationship(
        "UserSkill", back_populates="profile", cascade="all, delete-orphan"
    )
    educations: Mapped[list[Education]] = relationship(
        "Education", back_populates="profile", cascade="all, delete-orphan"
    )
    experiences: Mapped[list[WorkExperience]] = relationship(
        "WorkExperience", back_populates="profile", cascade="all, delete-orphan"
    )
    simulations: Mapped[list[Simulation]] = relationship(
        "Simulation", back_populates="profile", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_user_profiles_user_id", "user_id"),
        Index("ix_user_profiles_current_role_id", "current_role_id"),
    )

    def __repr__(self) -> str:
        return f"<UserProfile user_id={self.user_id!r}>"


class UserSkill(Base, TimestampMixin):
    """
    A skill the user claims to have, with self-assessed proficiency.

    proficiency_level: 1=Beginner → 5=Expert
    months_of_experience: how long they've been using this skill.
    is_self_assessed: True = declared by user; False = inferred/verified.
    """

    __tablename__ = "user_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    proficiency_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1-5
    months_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_self_assessed: Mapped[bool] = mapped_column(default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="user_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="user_skills")

    __table_args__ = (
        CheckConstraint(
            "proficiency_level BETWEEN 1 AND 5", name="ck_user_skill_proficiency"
        ),
        Index("ix_user_skills_profile_id", "profile_id"),
        Index("ix_user_skills_skill_id", "skill_id"),
        # One row per (profile, skill) pair
        Index("uq_user_skill", "profile_id", "skill_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<UserSkill profile={self.profile_id!r} "
            f"skill={self.skill_id!r} proficiency={self.proficiency_level}>"
        )


class Education(Base, TimestampMixin):
    """Formal education entries on a user's profile."""

    __tablename__ = "educations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    institution: Mapped[str] = mapped_column(String(300), nullable=False)
    degree: Mapped[str] = mapped_column(String(200), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="educations")

    __table_args__ = (Index("ix_educations_profile_id", "profile_id"),)

    def __repr__(self) -> str:
        return f"<Education {self.degree!r} @ {self.institution!r}>"


class WorkExperience(Base, TimestampMixin):
    """Work experience / project entries on a user's profile."""

    __tablename__ = "work_experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    company: Mapped[str | None] = mapped_column(String(300), nullable=True)   # null = personal project
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM
    end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)    # YYYY-MM or None=present
    is_current: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_project: Mapped[bool] = mapped_column(default=False, nullable=False)    # True = personal project

    # ── Relationships ─────────────────────────────────────────────────────────
    profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="experiences")

    __table_args__ = (Index("ix_work_experiences_profile_id", "profile_id"),)

    def __repr__(self) -> str:
        return f"<WorkExperience {self.title!r} @ {self.company!r}>"


# Circular import resolution
from app.models.role import Role  # noqa: E402, F401
from app.models.simulation import Simulation  # noqa: E402, F401
from app.models.skill import Skill  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
