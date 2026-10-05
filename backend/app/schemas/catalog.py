"""Response schemas for paginated public reference catalogs."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.role import RoleSkillRequirementRead, RoleSummary
from app.schemas.skill import SkillCategoryRead, SkillRead

CatalogItem = TypeVar("CatalogItem")


class CatalogPage(BaseModel, Generic[CatalogItem]):
    items: list[CatalogItem]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class RoleCatalogDetail(RoleSummary):
    model_config = ConfigDict(from_attributes=True)

    description: str | None = None
    avg_salary_inr: int | None = None
    avg_years_to_reach: float | None = None
    skill_requirements: list[RoleSkillRequirementRead] = []


class SkillCatalogItem(SkillRead):
    """A skill with its category included for catalog clients."""


class SkillCategoryCatalogItem(SkillCategoryRead):
    """A skill category with the number of skills it contains."""

    skill_count: int = Field(ge=0)
