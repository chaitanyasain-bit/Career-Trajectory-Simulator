"""
Import all ORM models here so SQLAlchemy's metadata is fully populated
and Alembic autogenerate can discover every table.

Import order is carefully set to avoid circular reference issues at load time.
"""

# ruff: noqa: I001

from app.db.base import Base  # noqa: F401 — re-export

# Reference tables (no FKs to other models)
from app.models.skill import Skill, SkillCategory  # noqa: F401
from app.models.role import Role, RoleSkillRequirement, RoleTransition  # noqa: F401

# User and profile models depend on Role and Skill.
from app.models.user import User  # noqa: F401
from app.models.profile import Education, UserProfile, UserSkill, WorkExperience  # noqa: F401

# Simulation models depend on UserProfile, Role, and Skill.
from app.models.simulation import (  # noqa: F401
    RoadmapStep,
    Simulation,
    SimulationPath,
    SkillGap,
)

__all__ = [
    "Base",
    "SkillCategory",
    "Skill",
    "Role",
    "RoleSkillRequirement",
    "RoleTransition",
    "User",
    "UserProfile",
    "UserSkill",
    "Education",
    "WorkExperience",
    "Simulation",
    "SimulationPath",
    "SkillGap",
    "RoadmapStep",
]
