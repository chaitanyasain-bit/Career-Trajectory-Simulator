"""
Database seeder logic.
Takes data from seed_data.py and upserts it into the database.
"""

import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.seed_data import (
    ROLE_SKILL_REQUIREMENTS,
    ROLE_TRANSITIONS,
    ROLES,
    SKILL_CATEGORIES,
    SKILLS,
)
from app.models import (
    Role,
    RoleSkillRequirement,
    RoleTransition,
    Skill,
    SkillCategory,
)

logger = logging.getLogger(__name__)


def validate_reference_data() -> None:
    """Fail before writing if the bundled career catalog contains invalid links."""
    errors: list[str] = []

    category_names = [item.get("name") for item in SKILL_CATEGORIES]
    if any(not isinstance(name, str) or not name.strip() for name in category_names):
        errors.append("Every skill category must have a non-empty name.")
    if len(category_names) != len(set(category_names)):
        errors.append("Skill category names must be unique.")
    if any(
        not isinstance(item.get("display_order"), int) or item["display_order"] < 0
        for item in SKILL_CATEGORIES
    ):
        errors.append("Skill category display_order values must be non-negative integers.")
    category_names_set = set(category_names)

    skill_names = [item.get("normalized_name") for item in SKILLS]
    if any(
        not isinstance(name, str) or re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", name) is None
        for name in skill_names
    ):
        errors.append("Skill normalized_name values must be lowercase underscore slugs.")
    if len(skill_names) != len(set(skill_names)):
        errors.append("Skill normalized_name values must be unique.")
    for item in SKILLS:
        if not item.get("name", "").strip():
            errors.append(f"Skill {item.get('normalized_name')!r} must have a display name.")
        if item.get("category") not in category_names_set:
            errors.append(
                f"Skill {item.get('normalized_name')!r} references unknown category "
                f"{item.get('category')!r}."
            )
    skill_names_set = set(skill_names)

    role_names = [item.get("normalized_title") for item in ROLES]
    if any(
        not isinstance(name, str) or re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", name) is None
        for name in role_names
    ):
        errors.append("Role normalized_title values must be lowercase underscore slugs.")
    if len(role_names) != len(set(role_names)):
        errors.append("Role normalized_title values must be unique.")
    for item in ROLES:
        if not item.get("title", "").strip():
            errors.append(f"Role {item.get('normalized_title')!r} must have a display title.")
        if item.get("seniority_level") not in range(1, 6):
            errors.append(f"Role {item.get('normalized_title')!r} has invalid seniority_level.")
        if item.get("avg_salary_inr") is not None and item["avg_salary_inr"] < 0:
            errors.append(f"Role {item.get('normalized_title')!r} has a negative salary.")
        if item.get("avg_years_to_reach") is not None and item["avg_years_to_reach"] < 0:
            errors.append(f"Role {item.get('normalized_title')!r} has negative years_to_reach.")
    role_names_set = set(role_names)

    requirement_keys: set[tuple[str, str]] = set()
    for item in ROLE_SKILL_REQUIREMENTS:
        if not isinstance(item, dict):
            errors.append(f"Role-skill requirement must be a mapping, got {item!r}.")
            continue
        key = (item.get("role"), item.get("skill"))
        if key in requirement_keys:
            errors.append(f"Duplicate role-skill requirement: {key!r}.")
        requirement_keys.add(key)
        if key[0] not in role_names_set or key[1] not in skill_names_set:
            errors.append(f"Role-skill requirement references unknown role or skill: {key!r}.")
        importance = item.get("importance", 3)
        if not isinstance(importance, int) or isinstance(importance, bool) or importance not in range(1, 6):
            errors.append(f"Role-skill requirement {key!r} has invalid importance.")
        target_level = item.get(
            "required_proficiency",
            max(1, importance - 1) if isinstance(importance, int) else 3,
        )
        if (
            not isinstance(target_level, int)
            or isinstance(target_level, bool)
            or target_level not in range(1, 6)
        ):
            errors.append(f"Role-skill requirement {key!r} has invalid required_proficiency.")
        if not isinstance(item.get("mandatory", True), bool):
            errors.append(f"Role-skill requirement {key!r} must set mandatory to a boolean.")

    transition_keys: set[tuple[str, str]] = set()
    for item in ROLE_TRANSITIONS:
        key = (item.get("from"), item.get("to"))
        if key in transition_keys:
            errors.append(f"Duplicate role transition: {key!r}.")
        transition_keys.add(key)
        if key[0] not in role_names_set or key[1] not in role_names_set:
            errors.append(f"Role transition references unknown role: {key!r}.")
        if key[0] == key[1]:
            errors.append(f"Role transition cannot point to itself: {key!r}.")
        weight = item.get("weight", 0.5)
        if not isinstance(weight, (int, float)) or not 0 <= weight <= 1:
            errors.append(f"Role transition {key!r} has invalid weight.")
        months = item.get("months")
        if months is not None and (not isinstance(months, int) or months < 1):
            errors.append(f"Role transition {key!r} has invalid months value.")

    if errors:
        raise ValueError("Invalid career reference data:\n- " + "\n- ".join(errors))


async def seed_database(session: AsyncSession) -> None:
    """Populates the database with initial reference data."""
    validate_reference_data()
    logger.info("Starting database seed...")

    # 1. Seed Skill Categories
    category_map = {}
    for cat_data in SKILL_CATEGORIES:
        data = dict(cat_data)
        stmt = select(SkillCategory).where(SkillCategory.name == data["name"])
        result = await session.execute(stmt)
        cat = result.scalar_one_or_none()
        if not cat:
            cat = SkillCategory(**data)
            session.add(cat)
        else:
            for k, v in data.items():
                setattr(cat, k, v)
        category_map[data["name"]] = cat

    await session.flush()
    logger.info("Seeded %d skill categories.", len(category_map))

    # 2. Seed Skills
    skill_map = {}
    for skill_data in SKILLS:
        data = dict(skill_data)
        cat_name = data.pop("category")
        category = category_map[cat_name]
        data["category_id"] = category.id

        stmt = select(Skill).where(Skill.normalized_name == data["normalized_name"])
        result = await session.execute(stmt)
        skill = result.scalar_one_or_none()

        if not skill:
            skill = Skill(**data)
            session.add(skill)
        else:
            for k, v in data.items():
                setattr(skill, k, v)
        skill_map[data["normalized_name"]] = skill

    await session.flush()
    logger.info("Seeded %d skills.", len(skill_map))

    # 3. Seed Roles
    role_map = {}
    for role_data in ROLES:
        data = dict(role_data)
        stmt = select(Role).where(Role.normalized_title == data["normalized_title"])
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            role = Role(**data)
            session.add(role)
        else:
            for k, v in data.items():
                setattr(role, k, v)
        role_map[data["normalized_title"]] = role

    await session.flush()
    logger.info("Seeded %d roles.", len(role_map))

    # 4. Seed Role-Skill Requirements
    req_count = 0
    for req_data in ROLE_SKILL_REQUIREMENTS:
        data = dict(req_data)
        role_norm = data.pop("role")
        skill_norm = data.pop("skill")

        role = role_map[role_norm]
        skill = skill_map[skill_norm]

        stmt = select(RoleSkillRequirement).where(
            RoleSkillRequirement.role_id == role.id,
            RoleSkillRequirement.skill_id == skill.id
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()

        importance = data.pop("importance", 3)
        mandatory = data.pop("mandatory", True)
        required_proficiency = data.pop(
            "required_proficiency",
            max(1, importance - 1),
        )

        if not req:
            req = RoleSkillRequirement(
                role_id=role.id,
                skill_id=skill.id,
                importance_level=importance,
                required_proficiency=required_proficiency,
                is_mandatory=mandatory,
                **data
            )
            session.add(req)
        else:
            req.importance_level = importance
            req.required_proficiency = required_proficiency
            req.is_mandatory = mandatory
            for k, v in data.items():
                setattr(req, k, v)
        req_count += 1

    await session.flush()
    logger.info("Seeded %d role-skill requirements.", req_count)

    # 5. Seed Role Transitions
    trans_count = 0
    for trans_data in ROLE_TRANSITIONS:
        data = dict(trans_data)
        from_norm = data.pop("from")
        to_norm = data.pop("to")

        from_role = role_map[from_norm]
        to_role = role_map[to_norm]

        stmt = select(RoleTransition).where(
            RoleTransition.from_role_id == from_role.id,
            RoleTransition.to_role_id == to_role.id
        )
        result = await session.execute(stmt)
        trans = result.scalar_one_or_none()

        if not trans:
            trans = RoleTransition(
                from_role_id=from_role.id,
                to_role_id=to_role.id,
                transition_weight=data.get("weight", 0.5),
                avg_transition_months=data.get("months")
            )
            session.add(trans)
        else:
            trans.transition_weight = data.get("weight", 0.5)
            trans.avg_transition_months = data.get("months")
        trans_count += 1

    await session.flush()
    logger.info("Seeded %d role transitions.", trans_count)

    await session.commit()
    logger.info("Database seed complete.")
