"""Authenticated career-profile management endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.models import (
    Education,
    Role,
    Skill,
    UserProfile,
    UserSkill,
    WorkExperience,
)
from app.schemas.profile import (
    ProjectCreate,
    UserProfileCreate,
    UserProfileRead,
    UserProfileUpdate,
    UserSkillCreate,
    WorkExperienceCreate,
)

router = APIRouter()


async def _load_profile(db: AsyncSession, user_id: str) -> UserProfile | None:
    result = await db.execute(
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
        .options(
            selectinload(UserProfile.user_skills).selectinload(UserSkill.skill),
            selectinload(UserProfile.educations),
            selectinload(UserProfile.experiences),
        )
    )
    return result.scalar_one_or_none()


def _profile_response(profile: UserProfile) -> UserProfileRead:
    return UserProfileRead.model_validate(
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "current_role_id": profile.current_role_id,
            "years_of_experience": profile.years_of_experience,
            "bio": profile.bio,
            "location": profile.location,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "user_skills": profile.user_skills,
            "educations": profile.educations,
            "experiences": [
                experience for experience in profile.experiences
                if not experience.is_project
            ],
            "projects": [
                experience for experience in profile.experiences
                if experience.is_project
            ],
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
    )


async def _validate_catalog_ids(
    db: AsyncSession,
    current_role_id: str | None,
    skills: list[UserSkillCreate] | None,
) -> None:
    if current_role_id is not None:
        role_exists = await db.scalar(select(Role.id).where(Role.id == current_role_id))
        if role_exists is None:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="current_role_id must refer to a role in the career catalog.",
            )

    skill_ids = {item.skill_id for item in skills or []}
    if skill_ids:
        existing_skill_ids = set(
            (
                await db.scalars(select(Skill.id).where(Skill.id.in_(skill_ids)))
            ).all()
        )
        missing_skill_ids = sorted(skill_ids - existing_skill_ids)
        if missing_skill_ids:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Every skill_id must refer to a skill in the catalog.",
                    "invalid_skill_ids": missing_skill_ids,
                },
            )


def _set_profile_fields(profile: UserProfile, values: dict[str, object]) -> None:
    scalar_fields = {
        "current_role_id",
        "years_of_experience",
        "bio",
        "location",
        "linkedin_url",
        "github_url",
    }
    for field in scalar_fields & values.keys():
        setattr(profile, field, values[field])

    if "skills" in values:
        skills = values["skills"]
        if isinstance(skills, list):
            profile.user_skills = [
                UserSkill(**item.model_dump()) for item in skills
            ]
    if "educations" in values:
        educations = values["educations"]
        if isinstance(educations, list):
            profile.educations = [
                Education(**item.model_dump()) for item in educations
            ]
    if "experiences" in values or "projects" in values:
        experiences = [
            item for item in profile.experiences
            if not item.is_project and "experiences" not in values
        ]
        projects = [
            item for item in profile.experiences
            if item.is_project and "projects" not in values
        ]
        for item in values.get("experiences", []):
            if isinstance(item, WorkExperienceCreate):
                experiences.append(WorkExperience(**item.model_dump(), is_project=False))
        for item in values.get("projects", []):
            if isinstance(item, ProjectCreate):
                projects.append(WorkExperience(**item.model_dump(), is_project=True))
        profile.experiences = [*experiences, *projects]


@router.get("/me", response_model=UserProfileRead)
async def get_my_profile(user: CurrentUser, db: DbSession) -> UserProfileRead:
    profile = await _load_profile(db, user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )
    return _profile_response(profile)


@router.post(
    "/me",
    response_model=UserProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_profile(
    payload: UserProfileCreate,
    user: CurrentUser,
    db: DbSession,
) -> UserProfileRead:
    if await _load_profile(db, user.id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile already exists for this account.",
        )

    await _validate_catalog_ids(db, payload.current_role_id, payload.skills)
    profile = UserProfile(user_id=user.id)
    values = payload.model_dump(
        exclude={"skills", "educations", "experiences", "projects"}
    )
    values.update(
        skills=payload.skills,
        educations=payload.educations,
        experiences=payload.experiences,
        projects=payload.projects,
    )
    _set_profile_fields(profile, values)
    db.add(profile)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile already exists for this account.",
        ) from None
    loaded_profile = await _load_profile(db, user.id)
    if loaded_profile is None:
        raise RuntimeError("Profile was committed but could not be reloaded.")
    return _profile_response(loaded_profile)


@router.patch("/me", response_model=UserProfileRead)
async def update_my_profile(
    payload: UserProfileUpdate,
    user: CurrentUser,
    db: DbSession,
) -> UserProfileRead:
    profile = await _load_profile(db, user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )

    values = payload.model_dump(
        exclude_unset=True,
        exclude={"skills", "educations", "experiences", "projects"},
    )
    for relationship in ("skills", "educations", "experiences", "projects"):
        if relationship in payload.model_fields_set:
            values[relationship] = getattr(payload, relationship)
    await _validate_catalog_ids(
        db,
        values.get("current_role_id", profile.current_role_id),
        values.get("skills"),
    )
    _set_profile_fields(profile, values)
    await db.commit()
    loaded_profile = await _load_profile(db, user.id)
    if loaded_profile is None:
        raise RuntimeError("Profile was committed but could not be reloaded.")
    return _profile_response(loaded_profile)
