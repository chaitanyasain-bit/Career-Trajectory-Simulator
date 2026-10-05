"""Authenticated career simulation and linked What-If endpoints."""

from __future__ import annotations

from copy import deepcopy
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DbSession
from app.models import Simulation, UserProfile
from app.schemas.simulation import (
    PathConfidenceChange,
    RoadmapChange,
    SimulationCreate,
    SimulationRead,
    SkillGapChange,
    WhatIfRequest,
    WhatIfResponse,
)
from app.services.simulation import (
    engine_profile_from_profile,
    engine_profile_from_snapshot,
    load_catalog,
    load_profile,
    load_simulation,
    persist_simulation,
    simulation_load_options,
)
from data.engine.trajectory import TrajectoryEngine

router = APIRouter()


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=message)


def _snapshot_engine(snapshot: dict[str, Any]) -> TrajectoryEngine:
    catalog = snapshot.get("catalog_snapshot")
    if not isinstance(catalog, dict) or not all(
        isinstance(catalog.get(name), list)
        for name in ("roles", "requirements", "transitions")
    ):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="This simulation does not contain a reproducible catalog snapshot.",
        )
    return TrajectoryEngine(
        catalog["roles"],
        catalog["transitions"],
        catalog["requirements"],
    )


@router.post(
    "/{profile_id}",
    response_model=SimulationRead,
    status_code=status.HTTP_201_CREATED,
)
async def run_simulation(
    profile_id: str,
    sim_in: SimulationCreate,
    db: DbSession,
    user: CurrentUser,
) -> SimulationRead:
    profile = await load_profile(db, profile_id, user_id=user.id)
    if profile is None:
        raise _not_found("Profile not found.")

    engine, catalog = await load_catalog(db)
    engine_profile = engine_profile_from_profile(profile)
    result = engine.simulate(engine_profile)
    simulation = await persist_simulation(
        db,
        profile=profile,
        catalog=catalog,
        engine_profile=engine_profile,
        result=result,
        label=sim_in.label,
        notes=sim_in.notes,
    )
    await db.commit()
    saved = await load_simulation(db, simulation.id)
    if saved is None:
        raise RuntimeError("Simulation was committed but could not be reloaded.")
    return saved


@router.post(
    "/{simulation_id}/whatif",
    response_model=WhatIfResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_whatif_simulation(
    simulation_id: str,
    whatif_in: WhatIfRequest,
    db: DbSession,
    user: CurrentUser,
) -> WhatIfResponse:
    baseline = await db.scalar(
        select(Simulation)
        .join(UserProfile, Simulation.profile_id == UserProfile.id)
        .where(Simulation.id == simulation_id, UserProfile.user_id == user.id)
        .options(*simulation_load_options())
    )
    if baseline is None:
        raise _not_found("Simulation not found.")

    snapshot = baseline.profile_snapshot
    scenario_engine = _snapshot_engine(snapshot)
    base_profile_data = snapshot.get("profile")
    catalog_snapshot = snapshot.get("catalog_snapshot", {})
    if not isinstance(base_profile_data, dict):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="This simulation does not contain a reproducible profile snapshot.",
        )
    scenario_profile = engine_profile_from_snapshot(snapshot)
    profile_skills = {
        item["skill_id"]: {
            "normalized_name": item["normalized_name"],
            "proficiency_level": int(item["proficiency_level"]),
            "months_of_experience": item.get("months_of_experience"),
        }
        for item in base_profile_data.get("skills", [])
        if item.get("skill_id") and item.get("normalized_name")
    }
    skills_by_id = {skill["id"]: skill for skill in catalog_snapshot.get("skills", [])}
    added_ids = set(whatif_in.add_skill_ids)
    invalid_skill_ids = sorted(added_ids - skills_by_id.keys())
    if invalid_skill_ids:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={
                "message": "Scenario skills must exist in the original simulation catalog.",
                "invalid_skill_ids": invalid_skill_ids,
            },
        )

    overrides = whatif_in.add_proficiency_overrides
    invalid_override_ids = sorted(set(overrides) - (profile_skills.keys() | added_ids))
    if invalid_override_ids:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={
                "message": (
                    "Proficiency can only be changed for a profile skill or a skill "
                    "added to this scenario."
                ),
                "invalid_skill_ids": invalid_override_ids,
            },
        )

    for skill_id in added_ids:
        skill = skills_by_id[skill_id]
        profile_skills.setdefault(
            skill_id,
            {
                "normalized_name": skill["normalized_name"],
                "proficiency_level": 3,
                "months_of_experience": None,
            },
        )
    for skill_id, proficiency in overrides.items():
        profile_skills[skill_id]["proficiency_level"] = proficiency
    scenario_profile.skills = {
        item["normalized_name"]: item["proficiency_level"]
        for item in profile_skills.values()
    }
    scenario_profile.skill_experience_months = {
        item["normalized_name"]: item["months_of_experience"]
        for item in profile_skills.values()
    }
    scenario_profile.years_of_experience += whatif_in.add_experience_months / 12
    added_projects = [
        {
            "title": project.title,
            "company": project.company,
            "description": project.description,
            "start_date": project.start_date,
        }
        for project in whatif_in.add_projects
    ]
    scenario_profile.projects = [*scenario_profile.projects, *added_projects]
    result = scenario_engine.simulate(scenario_profile)

    actual_profile = await load_profile(db, baseline.profile_id, user_id=user.id)
    if actual_profile is None:
        raise _not_found("Profile not found.")

    scenario_changes = whatif_in.model_dump(mode="json")
    scenario_snapshot = deepcopy(snapshot)
    scenario_snapshot["engine_input"] = {
        "current_role": scenario_profile.current_role,
        "skills": [
            {
                "normalized_name": name,
                "proficiency_level": level,
                "months_of_experience": scenario_profile.skill_experience_months.get(name),
            }
            for name, level in sorted(scenario_profile.skills.items())
        ],
        "years_of_experience": scenario_profile.years_of_experience,
        "projects": scenario_profile.projects,
        "educations": scenario_profile.educations,
        "experiences": scenario_profile.experiences,
        "bio": scenario_profile.bio,
        "location": scenario_profile.location,
    }
    scenario_snapshot["profile"]["skills"] = [
        {
            "skill_id": skill_id,
            "name": skills_by_id[skill_id]["name"],
            "normalized_name": skills_by_id[skill_id]["normalized_name"],
            "proficiency_level": profile_skills[skill_id]["proficiency_level"],
            "months_of_experience": profile_skills[skill_id]["months_of_experience"],
        }
        for skill_id in sorted(profile_skills)
    ]
    scenario_snapshot["profile"]["years_of_experience"] = (
        scenario_profile.years_of_experience
    )
    scenario_snapshot["profile"]["projects"] = [
        *scenario_snapshot["profile"].get("projects", []),
        *added_projects,
    ]
    scenario_snapshot["scenario_changes"] = scenario_changes

    _, live_catalog = await load_catalog(db)
    live_roles_by_id = {
        role.id: role for role in live_catalog["roles_by_name"].values()
    }
    live_skills_by_id = live_catalog["skills_by_id"]
    missing_role_ids = sorted(
        {role["id"] for role in catalog_snapshot["roles"]} - live_roles_by_id.keys()
    )
    missing_skill_ids = sorted(
        {skill["id"] for skill in catalog_snapshot["skills"]} - live_skills_by_id.keys()
    )
    if missing_role_ids or missing_skill_ids:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="A role or skill from the original simulation catalog is no longer available.",
        )
    frozen_catalog = {
        "catalog_snapshot": catalog_snapshot,
        "roles_by_name": {
            role["normalized_title"]: live_roles_by_id[role["id"]]
            for role in catalog_snapshot["roles"]
        },
        "skills_by_name": {
            skill["normalized_name"]: live_skills_by_id[skill["id"]]
            for skill in catalog_snapshot["skills"]
        },
        "skills_by_id": live_skills_by_id,
    }
    new_simulation = await persist_simulation(
        db,
        profile=actual_profile,
        catalog=frozen_catalog,
        engine_profile=scenario_profile,
        result=result,
        label=whatif_in.label or f"What-If from {baseline.label or baseline.id[:8]}",
        notes=f"What-If scenario linked to simulation {baseline.id}.",
        parent_simulation_id=baseline.id,
        scenario_changes=scenario_changes,
        input_snapshot_override=scenario_snapshot,
    )
    await db.commit()
    saved = await load_simulation(db, new_simulation.id)
    if saved is None:
        raise RuntimeError("What-If simulation was committed but could not be reloaded.")

    original_by_role = {
        path.target_role_id: path for path in baseline.paths
    }
    scenario_by_role = {path.target_role_id: path for path in saved.paths}
    role_title_by_id = {
        role["id"]: role["title"] for role in catalog_snapshot.get("roles", [])
    }
    confidence_changes: list[PathConfidenceChange] = []
    unlocked: list[str] = []
    improved: list[str] = []
    gap_changes: list[SkillGapChange] = []
    roadmap_changes: list[RoadmapChange] = []
    gap_names_by_id = {
        skill["id"]: skill["name"] for skill in catalog_snapshot.get("skills", [])
    }
    for role_id, scenario_path in scenario_by_role.items():
        original_path = original_by_role.get(role_id)
        role_title = role_title_by_id.get(
            role_id,
            scenario_path.engine_metadata.get("target_role_title", "Career role"),
        )
        old_score = original_path.confidence_score if original_path else None
        delta = scenario_path.confidence_score - (old_score or 0.0)
        confidence_changes.append(
            PathConfidenceChange(
                role_id=role_id,
                role_title=role_title,
                original_score=old_score,
                scenario_score=scenario_path.confidence_score,
                delta=round(delta, 4),
            )
        )
        if scenario_path.confidence_score >= 0.45 and (old_score or 0.0) < 0.45:
            unlocked.append(role_title)
        if old_score is not None and delta > 0.0001:
            improved.append(role_title)

        old_gaps = {
            gap.skill_id: gap
            for gap in (original_path.skill_gaps if original_path else [])
        }
        new_gaps = {gap.skill_id: gap for gap in scenario_path.skill_gaps}
        resolved = sorted(
            gap_names_by_id.get(skill_id, skill_id)
            for skill_id in old_gaps.keys() - new_gaps.keys()
        )
        newly_missing = sorted(
            gap_names_by_id.get(skill_id, skill_id)
            for skill_id in new_gaps.keys() - old_gaps.keys()
        )
        reduced = sorted(
            gap_names_by_id.get(skill_id, skill_id)
            for skill_id in old_gaps.keys() & new_gaps.keys()
            if new_gaps[skill_id].gap_score < old_gaps[skill_id].gap_score
        )
        if resolved or newly_missing or reduced:
            gap_changes.append(
                SkillGapChange(
                    role_id=role_id,
                    role_title=role_title,
                    newly_missing=newly_missing,
                    resolved=resolved,
                    improved=reduced,
                )
            )

        old_steps = {
            step.title for step in (original_path.roadmap_steps if original_path else [])
        }
        new_steps = {step.title for step in scenario_path.roadmap_steps}
        added_steps = sorted(new_steps - old_steps)
        removed_steps = sorted(old_steps - new_steps)
        if added_steps or removed_steps:
            roadmap_changes.append(
                RoadmapChange(
                    role_id=role_id,
                    role_title=role_title,
                    added_steps=added_steps,
                    removed_steps=removed_steps,
                )
            )

    confidence_changes.sort(key=lambda change: (-change.scenario_score, change.role_title))
    return WhatIfResponse(
        original_simulation_id=baseline.id,
        hypothetical_simulation=saved,
        newly_unlocked_roles=sorted(set(unlocked)),
        improved_confidence_roles=sorted(set(improved)),
        confidence_changes=confidence_changes,
        skill_gap_changes=gap_changes,
        roadmap_changes=roadmap_changes,
    )
