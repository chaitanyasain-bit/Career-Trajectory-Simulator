"""
Pydantic v2 schemas for Skill and SkillCategory.

Naming convention:
  <Entity>Base   — common fields (used for Create and Read)
  <Entity>Create — fields accepted on POST (omit server-generated fields)
  <Entity>Read   — full response schema (includes id, timestamps)
  <Entity>Update — PATCH schema (all fields Optional)
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ── SkillCategory ─────────────────────────────────────────────────────────────

class SkillCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    display_order: int = Field(default=0, ge=0)


class SkillCategoryCreate(SkillCategoryBase):
    pass


class SkillCategoryRead(SkillCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class SkillCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    display_order: int | None = Field(default=None, ge=0)


# ── Skill ─────────────────────────────────────────────────────────────────────

class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    normalized_name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    category_id: str


class SkillCreate(SkillBase):
    pass


class SkillRead(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    category: SkillCategoryRead | None = None


class SkillUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    category_id: str | None = None


class SkillSummary(BaseModel):
    """Lightweight reference used in nested responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    normalized_name: str
    category_id: str
