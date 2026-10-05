"""API contracts for career simulations, What-If scenarios, and roadmaps."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.role import RoleSummary
from app.schemas.skill import SkillSummary


class SkillGapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    skill_id: str
    skill: SkillSummary | None = None
    priority_rank: int
    gap_score: float = Field(ge=0.0, le=1.0)
    current_proficiency: int | None = Field(default=None, ge=0, le=5)
    required_proficiency: int | None = Field(default=None, ge=1, le=5)
    importance_level: int | None = Field(default=None, ge=1, le=5)
    is_mandatory: bool | None = None
    learning_resource: str | None = None
    notes: str | None = None


class RoadmapStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_order: int
    title: str
    description: str | None = None
    step_type: str
    estimated_weeks: int | None = None
    resource_url: str | None = None
    skill_id: str | None = None
    skill: SkillSummary | None = None


class SimulationPathRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    simulation_id: str
    target_role_id: str
    target_role: RoleSummary | None = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_label: str
    estimated_months: int | None = None
    rank: int
    engine_metadata: dict[str, Any] = Field(default_factory=dict)
    skill_gaps: list[SkillGapRead] = Field(default_factory=list)
    roadmap_steps: list[RoadmapStepRead] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def use_catalog_snapshots(cls, value: Any) -> Any:
        def get(item: Any, name: str, default: Any = None) -> Any:
            return item.get(name, default) if isinstance(item, dict) else getattr(item, name, default)

        metadata = get(value, "engine_metadata") or {}
        if not metadata:
            return value

        def nested_snapshot(items: list[Any]) -> list[dict[str, Any]]:
            snapshots = metadata.get("skill_snapshots", {})
            fields = (
                "id",
                "skill_id",
                "priority_rank",
                "gap_score",
                "current_proficiency",
                "required_proficiency",
                "importance_level",
                "is_mandatory",
                "learning_resource",
                "notes",
                "step_order",
                "title",
                "description",
                "step_type",
                "estimated_weeks",
                "resource_url",
            )
            return [
                {
                    **{
                        name: get(item, name)
                        for name in fields
                        if get(item, name) is not None
                    },
                    "skill": snapshots.get(get(item, "skill_id")),
                }
                for item in items
            ]

        data = {
            name: get(value, name)
            for name in (
                "id",
                "simulation_id",
                "target_role_id",
                "confidence_score",
                "confidence_label",
                "estimated_months",
                "rank",
            )
        }
        data["engine_metadata"] = metadata
        data["target_role"] = metadata.get(
            "target_role_snapshot",
            get(value, "target_role"),
        )
        data["skill_gaps"] = nested_snapshot(get(value, "skill_gaps", []))
        data["roadmap_steps"] = nested_snapshot(get(value, "roadmap_steps", []))
        return data


class SimulationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)


class SimulationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    profile_id: str
    parent_simulation_id: str | None = None
    label: str | None = None
    engine_version: str
    notes: str | None = None
    paths: list[SimulationPathRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SimulationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_simulation_id: str | None = None
    label: str | None = None
    engine_version: str
    path_count: int = 0
    created_at: datetime


class WhatIfProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=3000)
    start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")

    @field_validator("start_date")
    @classmethod
    def validate_month(cls, value: str | None) -> str | None:
        if value is not None:
            datetime.strptime(value, "%Y-%m")
        return value

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Project title cannot be blank.")
        return value


class WhatIfRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    add_skill_ids: list[str] = Field(default_factory=list, max_length=100)
    add_proficiency_overrides: dict[str, Annotated[int, Field(ge=1, le=5)]] = Field(
        default_factory=dict,
        max_length=100,
    )
    add_experience_months: int = Field(default=0, ge=0, le=720)
    add_projects: list[WhatIfProject] = Field(default_factory=list, max_length=20)
    label: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_skill_ids(self) -> WhatIfRequest:
        if len(self.add_skill_ids) != len(set(self.add_skill_ids)):
            raise ValueError("A scenario cannot add the same skill more than once.")
        if any(not skill_id.strip() for skill_id in self.add_skill_ids):
            raise ValueError("Skill IDs cannot be blank.")
        if any(not skill_id.strip() for skill_id in self.add_proficiency_overrides):
            raise ValueError("Proficiency override skill IDs cannot be blank.")
        return self


class PathConfidenceChange(BaseModel):
    role_id: str
    role_title: str
    original_score: float | None = Field(ge=0.0, le=1.0)
    scenario_score: float = Field(ge=0.0, le=1.0)
    delta: float = Field(ge=-1.0, le=1.0)


class SkillGapChange(BaseModel):
    role_id: str
    role_title: str
    newly_missing: list[str] = Field(default_factory=list)
    resolved: list[str] = Field(default_factory=list)
    improved: list[str] = Field(default_factory=list)


class RoadmapChange(BaseModel):
    role_id: str
    role_title: str
    added_steps: list[str] = Field(default_factory=list)
    removed_steps: list[str] = Field(default_factory=list)


class WhatIfResponse(BaseModel):
    original_simulation_id: str
    hypothetical_simulation: SimulationRead
    newly_unlocked_roles: list[str] = Field(default_factory=list)
    improved_confidence_roles: list[str] = Field(default_factory=list)
    confidence_changes: list[PathConfidenceChange] = Field(default_factory=list)
    skill_gap_changes: list[SkillGapChange] = Field(default_factory=list)
    roadmap_changes: list[RoadmapChange] = Field(default_factory=list)
