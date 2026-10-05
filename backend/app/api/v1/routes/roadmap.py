"""Retrieve persisted roadmap steps for an owned career path."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.models import RoadmapStep, Simulation, SimulationPath, UserProfile
from app.schemas.simulation import RoadmapStepRead

router = APIRouter()


@router.get("/{path_id}", response_model=list[RoadmapStepRead])
async def get_roadmap(
    path_id: str,
    db: DbSession,
    user: CurrentUser,
):
    """Return saved roadmap steps without regenerating historical results."""
    path = await db.scalar(
        select(SimulationPath)
        .join(Simulation, SimulationPath.simulation_id == Simulation.id)
        .join(UserProfile, Simulation.profile_id == UserProfile.id)
        .where(
            SimulationPath.id == path_id,
            UserProfile.user_id == user.id,
        )
    )
    if path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation path not found.",
        )

    stmt = (
        select(RoadmapStep)
        .where(RoadmapStep.simulation_path_id == path_id)
        .order_by(RoadmapStep.step_order.asc())
        .options(selectinload(RoadmapStep.skill))
    )
    result = await db.execute(stmt)
    steps = result.scalars().all()

    return steps
