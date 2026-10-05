"""Read-only endpoints for career roles, skills, and skill categories."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Role, RoleSkillRequirement, Skill, SkillCategory
from app.schemas.catalog import (
    CatalogPage,
    RoleCatalogDetail,
    SkillCatalogItem,
    SkillCategoryCatalogItem,
)
from app.schemas.role import RoleSummary

router = APIRouter()
DbSession = Annotated[AsyncSession, Depends(get_db)]
PageLimit = Annotated[int, Query(ge=1, le=100)]
PageOffset = Annotated[int, Query(ge=0)]
SearchTerm = Annotated[str | None, Query(min_length=1, max_length=100)]


@router.get("/roles", response_model=CatalogPage[RoleSummary])
async def list_roles(
    db: DbSession,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    search: SearchTerm = None,
    domain: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
) -> CatalogPage[RoleSummary]:
    filters = []
    search = search.strip() if search and search.strip() else None
    domain = domain.strip() if domain and domain.strip() else None
    if search:
        pattern = f"%{search}%"
        filters.append(
            or_(Role.title.ilike(pattern), Role.normalized_title.ilike(pattern))
        )
    if domain:
        filters.append(Role.domain.ilike(domain))

    total = await db.scalar(select(func.count()).select_from(Role).where(*filters))
    roles = await db.scalars(
        select(Role)
        .where(*filters)
        .order_by(Role.title.asc(), Role.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return CatalogPage(
        items=list(roles.all()),
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/roles/{role_id}", response_model=RoleCatalogDetail)
async def get_role(role_id: str, db: DbSession) -> Role:
    role = await db.scalar(
        select(Role)
        .where(Role.id == role_id)
        .options(
            selectinload(Role.skill_requirements).selectinload(RoleSkillRequirement.skill)
        )
    )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


@router.get("/skills", response_model=CatalogPage[SkillCatalogItem])
async def list_skills(
    db: DbSession,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    search: SearchTerm = None,
    category_id: Annotated[str | None, Query(min_length=1, max_length=36)] = None,
) -> CatalogPage[SkillCatalogItem]:
    filters = []
    search = search.strip() if search and search.strip() else None
    if search:
        pattern = f"%{search}%"
        filters.append(
            or_(Skill.name.ilike(pattern), Skill.normalized_name.ilike(pattern))
        )
    if category_id:
        filters.append(Skill.category_id == category_id)

    total = await db.scalar(select(func.count()).select_from(Skill).where(*filters))
    skills = await db.scalars(
        select(Skill)
        .where(*filters)
        .options(selectinload(Skill.category))
        .order_by(Skill.name.asc(), Skill.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return CatalogPage(
        items=list(skills.all()),
        total=total or 0,
        limit=limit,
        offset=offset,
    )


@router.get("/skills/{skill_id}", response_model=SkillCatalogItem)
async def get_skill(skill_id: str, db: DbSession) -> Skill:
    skill = await db.scalar(
        select(Skill)
        .where(Skill.id == skill_id)
        .options(selectinload(Skill.category))
    )
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found",
        )
    return skill


@router.get(
    "/skill-categories",
    response_model=CatalogPage[SkillCategoryCatalogItem],
)
async def list_skill_categories(
    db: DbSession,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    search: SearchTerm = None,
) -> CatalogPage[SkillCategoryCatalogItem]:
    filters = []
    search = search.strip() if search and search.strip() else None
    if search:
        pattern = f"%{search}%"
        filters.append(
            or_(
                SkillCategory.name.ilike(pattern),
                SkillCategory.description.ilike(pattern),
            )
        )

    total = await db.scalar(
        select(func.count()).select_from(SkillCategory).where(*filters)
    )
    rows = await db.execute(
        select(
            SkillCategory,
            func.count(Skill.id).label("skill_count"),
        )
        .outerjoin(Skill, Skill.category_id == SkillCategory.id)
        .where(*filters)
        .group_by(SkillCategory.id)
        .order_by(SkillCategory.display_order.asc(), SkillCategory.name.asc())
        .limit(limit)
        .offset(offset)
    )
    items = [
        SkillCategoryCatalogItem.model_validate(
            {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "display_order": category.display_order,
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "skill_count": skill_count,
            }
        )
        for category, skill_count in rows.all()
    ]
    return CatalogPage(items=items, total=total or 0, limit=limit, offset=offset)


@router.get(
    "/skill-categories/{category_id}",
    response_model=SkillCategoryCatalogItem,
)
async def get_skill_category(
    category_id: str,
    db: DbSession,
) -> SkillCategoryCatalogItem:
    row = await db.execute(
        select(
            SkillCategory,
            func.count(Skill.id).label("skill_count"),
        )
        .outerjoin(Skill, Skill.category_id == SkillCategory.id)
        .where(SkillCategory.id == category_id)
        .group_by(SkillCategory.id)
    )
    result = row.one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill category not found",
        )

    category, skill_count = result
    return SkillCategoryCatalogItem.model_validate(
        {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "display_order": category.display_order,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "skill_count": skill_count,
        }
    )
