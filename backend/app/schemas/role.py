"""
Pydantic v2 schemas for Role, RoleSkillRequirement, and RoleTransition.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.skill import SkillSummary

# ── Role ──────────────────────────────────────────────────────────────────────

class RoleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    normalized_title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    domain: str | None = Field(default=None, max_length=100)
    seniority_level: int = Field(default=2, ge=1, le=5)
    avg_salary_inr: int | None = Field(default=None, ge=0)
    avg_years_to_reach: float | None = Field(default=None, ge=0)


class RoleCreate(RoleBase):
    pass


class RoleRead(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class RoleReadWithSkills(RoleRead):
    """Role with its required skills expanded."""
    skill_requirements: list[RoleSkillRequirementRead] = []


class RoleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    domain: str | None = None
    seniority_level: int | None = Field(default=None, ge=1, le=5)
    avg_salary_inr: int | None = None
    avg_years_to_reach: float | None = None


class RoleSummary(BaseModel):
    """Lightweight reference for nested use."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    normalized_title: str
    domain: str | None = None
    seniority_level: int


# ── RoleSkillRequirement ──────────────────────────────────────────────────────

class RoleSkillRequirementBase(BaseModel):
    role_id: str
    skill_id: str
    importance_level: int = Field(default=3, ge=1, le=5)
    required_proficiency: int = Field(default=3, ge=1, le=5)
    is_mandatory: bool = True
    notes: str | None = None


class RoleSkillRequirementCreate(RoleSkillRequirementBase):
    pass


class RoleSkillRequirementRead(RoleSkillRequirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    skill: SkillSummary | None = None
    created_at: datetime
    updated_at: datetime


# ── RoleTransition ────────────────────────────────────────────────────────────

class RoleTransitionBase(BaseModel):
    from_role_id: str
    to_role_id: str
    transition_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    avg_transition_months: int | None = Field(default=None, ge=1)
    notes: str | None = None


class RoleTransitionCreate(RoleTransitionBase):
    pass


class RoleTransitionRead(RoleTransitionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_role: RoleSummary | None = None
    to_role: RoleSummary | None = None
    created_at: datetime
    updated_at: datetime


# Self-referential resolution
RoleReadWithSkills.model_rebuild()
