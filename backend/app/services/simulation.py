"""Database-backed catalog, profile snapshot, and simulation persistence helpers."""

from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    RoadmapStep,
    Role,
    RoleSkillRequirement,
    RoleTransition,
    Simulation,
    SimulationPath,
    Skill,
    SkillGap,
    UserProfile,
    UserSkill,
    WorkExperience,
)
from data.engine.roadmap import generate_roadmap
from data.engine.trajectory import (
    ENGINE_VERSION,
    CareerPath,
    SimulationResult,
    TrajectoryEngine,
)
from data.engine.trajectory import (
    UserProfile as EngineUserProfile,
)


async def load_profile(
    db: AsyncSession,
    profile_id: str,
    *,
    user_id: str | None = None,
) -> UserProfile | None:
    query = select(UserProfile).where(UserProfile.id == profile_id)
    if user_id is not None:
        query = query.where(UserProfile.user_id == user_id)
    query = query.options(
        selectinload(UserProfile.current_role),
        selectinload(UserProfile.user_skills)
        .selectinload(UserSkill.skill)
        .selectinload(Skill.category),
        selectinload(UserProfile.educations),
        selectinload(UserProfile.experiences),
    )
    return (await db.execute(query)).scalar_one_or_none()


async def load_catalog(db: AsyncSession) -> tuple[TrajectoryEngine, dict[str, Any]]:
    roles = list(
        (
            await db.scalars(
                select(Role)
                .options(
                    selectinload(Role.skill_requirements)
                    .selectinload(RoleSkillRequirement.skill)
                    .selectinload(Skill.category)
                )
                .order_by(Role.normalized_title)
            )
        ).all()
    )
    transitions = list(
        (
            await db.scalars(
                select(RoleTransition)
                .options(
                    selectinload(RoleTransition.from_role),
                    selectinload(RoleTransition.to_role),
                )
                .order_by(RoleTransition.from_role_id, RoleTransition.to_role_id)
            )
        ).all()
    )
    skills = list(
        (
            await db.scalars(
                select(Skill).options(selectinload(Skill.category)).order_by(Skill.normalized_name)
            )
        ).all()
    )
    engine_roles = [
        {
            "id": role.id,
            "title": role.title,
            "normalized_title": role.normalized_title,
            "domain": role.domain,
            "seniority_level": role.seniority_level,
            "avg_years_to_reach": role.avg_years_to_reach,
            "avg_salary_inr": role.avg_salary_inr,
        }
        for role in roles
    ]
    engine_transitions = [
        {
            "from": transition.from_role.normalized_title,
            "to": transition.to_role.normalized_title,
            "weight": transition.transition_weight,
            "months": transition.avg_transition_months or 12,
            "notes": transition.notes,
        }
        for transition in transitions
    ]
    engine_requirements: list[dict[str, Any]] = []
    for role in roles:
        for requirement in role.skill_requirements:
            engine_requirements.append(
                {
                    "role": role.normalized_title,
                    "skill": requirement.skill.normalized_name,
                    "skill_id": requirement.skill_id,
                    "category": requirement.skill.category.name,
                    "importance": requirement.importance_level,
                    "mandatory": requirement.is_mandatory,
                    "required_proficiency": requirement.required_proficiency,
                    "notes": requirement.notes,
                }
            )

    catalog_snapshot = {
        "roles": engine_roles,
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "normalized_name": skill.normalized_name,
                "category_id": skill.category_id,
                "category": skill.category.name,
            }
            for skill in skills
        ],
        "requirements": engine_requirements,
        "transitions": [
            {
                "from_role_id": transition.from_role_id,
                "to_role_id": transition.to_role_id,
                **transition_data,
            }
            for transition, transition_data in zip(
                transitions, engine_transitions, strict=True
            )
        ],
    }
    return (
        TrajectoryEngine(engine_roles, engine_transitions, engine_requirements),
        {
            "roles_by_name": {role.normalized_title: role for role in roles},
            "skills_by_name": {skill.normalized_name: skill for skill in skills},
            "skills_by_id": {skill.id: skill for skill in skills},
            "catalog_snapshot": catalog_snapshot,
        },
    )


def _employment_years(experiences: Sequence[WorkExperience]) -> float:
    intervals: list[tuple[int, int]] = []
    current = date.today()
    for experience in experiences:
        if experience.is_project or experience.start_date is None:
            continue
        year_text, month_text = experience.start_date.split("-")
        start = (int(year_text) * 12) + int(month_text) - 1
        if experience.is_current or experience.end_date is None:
            end = (current.year * 12) + current.month - 1
        else:
            end_year, end_month = map(int, experience.end_date.split("-"))
            end = (end_year * 12) + end_month - 1
        if end >= start:
            intervals.append((start, end))
    if not intervals:
        return 0.0
    intervals.sort()
    start, end = intervals[0]
    total_months = 0
    for next_start, next_end in intervals[1:]:
        if next_start <= end + 1:
            end = max(end, next_end)
        else:
            total_months += end - start + 1
            start, end = next_start, next_end
    total_months += end - start + 1
    return total_months / 12


def engine_profile_from_profile(profile: UserProfile) -> EngineUserProfile:
    skill_levels = {
        user_skill.skill.normalized_name: user_skill.proficiency_level
        for user_skill in profile.user_skills
        if user_skill.skill is not None
    }
    skill_months = {
        user_skill.skill.normalized_name: user_skill.months_of_experience
        for user_skill in profile.user_skills
        if user_skill.skill is not None
    }
    role = profile.current_role
    work = [item for item in profile.experiences if not item.is_project]
    projects = [item for item in profile.experiences if item.is_project]
    return EngineUserProfile(
        current_role=role.normalized_title if role else None,
        skills=skill_levels,
        skill_experience_months=skill_months,
        years_of_experience=max(profile.years_of_experience, _employment_years(work)),
        projects=[
            {
                "title": item.title,
                "company": item.company,
                "description": item.description,
                "start_date": item.start_date,
            }
            for item in projects
        ],
        educations=[
            {
                "degree": item.degree,
                "field_of_study": item.field_of_study,
                "end_year": item.end_year,
                "is_current": item.is_current,
            }
            for item in profile.educations
        ],
        experiences=[
            {
                "title": item.title,
                "company": item.company,
                "description": item.description,
                "start_date": item.start_date,
                "end_date": item.end_date,
                "is_current": item.is_current,
            }
            for item in work
        ],
        bio=profile.bio,
        location=profile.location,
    )


def engine_profile_from_snapshot(snapshot: dict[str, Any]) -> EngineUserProfile:
    engine_input = snapshot.get("engine_input")
    if not isinstance(engine_input, dict):
        raise ValueError("This saved simulation does not contain reproducible inputs.")
    return EngineUserProfile(
        current_role=engine_input.get("current_role"),
        skills={
            item["normalized_name"]: int(item["proficiency_level"])
            for item in engine_input.get("skills", [])
        },
        skill_experience_months={
            item["normalized_name"]: item.get("months_of_experience")
            for item in engine_input.get("skills", [])
        },
        years_of_experience=float(engine_input.get("years_of_experience", 0)),
        projects=list(engine_input.get("projects", [])),
        educations=list(engine_input.get("educations", [])),
        experiences=list(engine_input.get("experiences", [])),
        bio=engine_input.get("bio"),
        location=engine_input.get("location"),
    )


def _input_snapshot(
    profile: UserProfile,
    catalog_snapshot: dict[str, Any],
    engine_profile: EngineUserProfile,
    *,
    scenario_changes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    role = profile.current_role
    return {
        "profile": {
            "profile_id": profile.id,
            "current_role": (
                {
                    "id": role.id,
                    "title": role.title,
                    "normalized_title": role.normalized_title,
                }
                if role
                else None
            ),
            "years_of_experience": profile.years_of_experience,
            "bio": profile.bio,
            "location": profile.location,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "skills": [
                {
                    "skill_id": item.skill_id,
                    "name": item.skill.name if item.skill else None,
                    "normalized_name": (
                        item.skill.normalized_name if item.skill else None
                    ),
                    "proficiency_level": item.proficiency_level,
                    "months_of_experience": item.months_of_experience,
                }
                for item in profile.user_skills
            ],
            "educations": [
                {
                    "institution": item.institution,
                    "degree": item.degree,
                    "field_of_study": item.field_of_study,
                    "start_year": item.start_year,
                    "end_year": item.end_year,
                    "is_current": item.is_current,
                }
                for item in profile.educations
            ],
            "experiences": [
                {
                    "title": item.title,
                    "company": item.company,
                    "description": item.description,
                    "start_date": item.start_date,
                    "end_date": item.end_date,
                    "is_current": item.is_current,
                }
                for item in profile.experiences
                if not item.is_project
            ],
            "projects": [
                {
                    "title": item.title,
                    "description": item.description,
                    "start_date": item.start_date,
                }
                for item in profile.experiences
                if item.is_project
            ],
        },
        "engine_input": {
            "current_role": engine_profile.current_role,
            "skills": [
                {
                    "normalized_name": name,
                    "proficiency_level": proficiency,
                    "months_of_experience": engine_profile.skill_experience_months.get(name),
                }
                for name, proficiency in sorted(engine_profile.skills.items())
            ],
            "years_of_experience": engine_profile.years_of_experience,
            "projects": engine_profile.projects,
            "educations": engine_profile.educations,
            "experiences": engine_profile.experiences,
            "bio": engine_profile.bio,
            "location": engine_profile.location,
        },
        "catalog_snapshot": catalog_snapshot,
        "engine_version": ENGINE_VERSION,
        "scenario_changes": scenario_changes,
    }


def _path_metadata(path: CareerPath, catalog: dict[str, Any]) -> dict[str, Any]:
    role = catalog["roles_by_name"].get(path.target_role)
    metadata = deepcopy(path.engine_metadata)
    if role is not None:
        metadata["target_role_snapshot"] = {
            "id": role.id,
            "title": role.title,
            "normalized_title": role.normalized_title,
            "domain": role.domain,
            "seniority_level": role.seniority_level,
        }
    metadata["skill_snapshots"] = {
        skill.id: {
            "id": skill.id,
            "name": skill.name,
            "normalized_name": skill.normalized_name,
            "category_id": skill.category_id,
        }
        for gap in path.skill_gaps
        if (skill := catalog["skills_by_name"].get(gap.skill)) is not None
    }
    return metadata


def _result_snapshot(
    result: SimulationResult,
    catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    snapshots = []
    for path in result.paths:
        target_role = catalog["roles_by_name"].get(path.target_role)
        roadmap = generate_roadmap(
            path.skill_gaps,
            target_role.title if target_role else path.target_role,
        )
        learning_resources = {
            step.skill_id: step.resource_url
            for step in roadmap
            if step.skill_id and step.resource_url
        }
        snapshots.append({
            "target_role": path.target_role,
            "target_role_title": path.engine_metadata["target_role_title"],
            "confidence_score": path.confidence,
            "confidence_label": path.confidence_label,
            "estimated_months": path.estimated_months,
            "engine_metadata": _path_metadata(path, catalog),
            "skill_gaps": [
                {
                    "skill": gap.skill,
                    "skill_id": gap.skill_id,
                    "priority": gap.priority,
                    "gap_score": gap.gap_score,
                    "current_proficiency": gap.current_proficiency,
                    "required_proficiency": gap.required_proficiency,
                    "importance_level": gap.importance_level,
                    "is_mandatory": gap.is_mandatory,
                    "reason": gap.reason,
                    "learning_resource": learning_resources.get(gap.skill_id),
                    "skill_name": catalog["skills_by_name"][gap.skill].name,
                    "skill_category": catalog["skills_by_name"][gap.skill].category.name,
                }
                for gap in path.skill_gaps
            ],
        })
    return snapshots


async def persist_simulation(
    db: AsyncSession,
    *,
    profile: UserProfile,
    catalog: dict[str, Any],
    engine_profile: EngineUserProfile,
    result: SimulationResult,
    label: str | None,
    notes: str | None,
    parent_simulation_id: str | None = None,
    scenario_changes: dict[str, Any] | None = None,
    input_snapshot_override: dict[str, Any] | None = None,
) -> Simulation:
    snapshot = (
        deepcopy(input_snapshot_override)
        if input_snapshot_override is not None
        else _input_snapshot(
            profile,
            catalog["catalog_snapshot"],
            engine_profile,
            scenario_changes=scenario_changes,
        )
    )
    snapshot["engine_output"] = _result_snapshot(result, catalog)
    simulation = Simulation(
        profile_id=profile.id,
        parent_simulation_id=parent_simulation_id,
        label=label,
        engine_version=ENGINE_VERSION,
        notes=notes,
        profile_snapshot=snapshot,
    )
    db.add(simulation)
    await db.flush()

    for rank, path in enumerate(result.paths, start=1):
        target_role = catalog["roles_by_name"].get(path.target_role)
        if target_role is None:
            continue
        stored_path = SimulationPath(
            simulation_id=simulation.id,
            target_role_id=target_role.id,
            confidence_score=path.confidence,
            confidence_label=path.confidence_label,
            estimated_months=path.estimated_months,
            rank=rank,
            engine_metadata=_path_metadata(path, catalog),
        )
        db.add(stored_path)
        await db.flush()

        roadmap = generate_roadmap(path.skill_gaps, target_role.title)
        learning_resources = {
            step.skill_id: step.resource_url
            for step in roadmap
            if step.skill_id and step.resource_url
        }
        for priority_rank, gap in enumerate(path.skill_gaps, start=1):
            skill = catalog["skills_by_name"].get(gap.skill)
            if skill is None:
                continue
            db.add(
                SkillGap(
                    simulation_path_id=stored_path.id,
                    skill_id=skill.id,
                    priority_rank=priority_rank,
                    gap_score=gap.gap_score,
                    current_proficiency=gap.current_proficiency,
                    required_proficiency=gap.required_proficiency,
                    importance_level=gap.importance_level,
                    is_mandatory=gap.is_mandatory,
                    learning_resource=learning_resources.get(skill.id),
                    notes=gap.reason,
                )
            )
        for step_order, step in enumerate(roadmap, start=1):
            db.add(
                RoadmapStep(
                    simulation_path_id=stored_path.id,
                    step_order=step_order,
                    title=step.title,
                    description=step.description,
                    step_type=step.step_type,
                    estimated_weeks=step.estimated_weeks,
                    resource_url=step.resource_url,
                    skill_id=step.skill_id,
                )
            )
    await db.flush()
    return simulation


def simulation_load_options():
    return (
        selectinload(Simulation.paths).selectinload(SimulationPath.target_role),
        selectinload(Simulation.paths)
        .selectinload(SimulationPath.skill_gaps)
        .selectinload(SkillGap.skill),
        selectinload(Simulation.paths)
        .selectinload(SimulationPath.roadmap_steps)
        .selectinload(RoadmapStep.skill),
    )


async def load_simulation(db: AsyncSession, simulation_id: str) -> Simulation | None:
    return (
        await db.execute(
            select(Simulation)
            .where(Simulation.id == simulation_id)
            .options(*simulation_load_options())
        )
    ).scalar_one_or_none()
