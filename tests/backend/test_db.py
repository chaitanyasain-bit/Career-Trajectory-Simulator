"""
Tests for the database layer, models, and schemas using an in-memory SQLite DB.
"""

import pytest
from app.config import Settings
from app.db.health import check_db_connection
from app.db.seed import seed_database, validate_reference_data
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
from app.schemas.profile import UserProfileCreate, UserSkillCreate
from app.schemas.skill import SkillCategoryCreate
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_health_check():
    """Test the database health check function."""
    status = await check_db_connection()
    assert status["status"] == "ok"
    assert status["detail"] is None

@pytest.mark.asyncio
async def test_seed_and_models(db: AsyncSession):
    """Test that seed data loads correctly and models map as expected."""
    # Seed the database
    await seed_database(db)

    # Validate Skill Categories
    result = await db.execute(text("SELECT COUNT(*) FROM skill_categories"))
    cat_count = result.scalar()
    assert cat_count > 0, "No skill categories seeded."

    # Validate Skills
    result = await db.execute(text("SELECT COUNT(*) FROM skills"))
    skill_count = result.scalar()
    assert skill_count > 0, "No skills seeded."

    # Validate Roles
    result = await db.execute(text("SELECT COUNT(*) FROM roles"))
    role_count = result.scalar()
    assert role_count > 0, "No roles seeded."

    # Validate RoleSkillRequirements
    result = await db.execute(text("SELECT COUNT(*) FROM role_skill_requirements"))
    req_count = result.scalar()
    assert req_count > 0, "No role skill requirements seeded."
    requirements = (await db.scalars(select(RoleSkillRequirement))).all()
    assert all(1 <= req.required_proficiency <= 5 for req in requirements)

    # Validate RoleTransitions
    result = await db.execute(text("SELECT COUNT(*) FROM role_transitions"))
    trans_count = result.scalar()
    assert trans_count > 0, "No role transitions seeded."


@pytest.mark.asyncio
async def test_seed_is_repeatable(db: AsyncSession):
    """Repeated seeding updates reference rows instead of duplicating them."""
    await seed_database(db)
    catalog_models = (SkillCategory, Skill, Role, RoleSkillRequirement, RoleTransition)
    first_ids = {
        model: (await db.scalars(select(model.id).order_by(model.id))).all()
        for model in catalog_models
    }
    first_proficiencies = {
        req.id: req.required_proficiency
        for req in (await db.scalars(select(RoleSkillRequirement))).all()
    }

    await seed_database(db)
    second_ids = {
        model: (await db.scalars(select(model.id).order_by(model.id))).all()
        for model in catalog_models
    }
    second_proficiencies = {
        req.id: req.required_proficiency
        for req in (await db.scalars(select(RoleSkillRequirement))).all()
    }
    counts = {
        model: await db.scalar(select(func.count()).select_from(model))
        for model in catalog_models
    }

    assert second_ids == first_ids
    assert second_proficiencies == first_proficiencies
    assert counts == {
        SkillCategory: len(SKILL_CATEGORIES),
        Skill: len(SKILLS),
        Role: len(ROLES),
        RoleSkillRequirement: len(ROLE_SKILL_REQUIREMENTS),
        RoleTransition: len(ROLE_TRANSITIONS),
    }


def test_reference_data_is_valid():
    validate_reference_data()


def test_application_database_default_is_postgresql(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")


@pytest.mark.asyncio
async def test_schema_validation():
    """Test Pydantic schema validation."""
    # Valid SkillCategoryCreate
    cat_data = {"name": "Test Category", "description": "Test", "display_order": 1}
    cat_schema = SkillCategoryCreate(**cat_data)
    assert cat_schema.name == "Test Category"

    # Valid UserProfileCreate with nested skills
    profile_data = {
        "years_of_experience": 2.5,
        "skills": [
            {"skill_id": "fake-uuid-1", "proficiency_level": 4},
            {"skill_id": "fake-uuid-2", "proficiency_level": 3, "months_of_experience": 12}
        ]
    }
    profile_schema = UserProfileCreate(**profile_data)
    assert profile_schema.years_of_experience == 2.5
    assert len(profile_schema.skills) == 2
    assert profile_schema.skills[0].proficiency_level == 4

    # Invalid proficiency level (out of bounds)
    try:
        UserSkillCreate(skill_id="fake", proficiency_level=10)
        assert False, "Should have raised a validation error for proficiency_level > 5"
    except ValueError:
        pass
