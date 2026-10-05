"""Access and replay persisted simulation results without recalculation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.models import Simulation, UserProfile
from app.schemas.simulation import SimulationRead, SimulationSummary
from app.services.simulation import simulation_load_options

router = APIRouter()


async def _owned_simulation(
    simulation_id: str,
    user_id: str,
    db: DbSession,
) -> Simulation | None:
    result = await db.execute(
        select(Simulation)
        .join(UserProfile, Simulation.profile_id == UserProfile.id)
        .where(Simulation.id == simulation_id, UserProfile.user_id == user_id)
        .options(*simulation_load_options())
    )
    return result.scalar_one_or_none()


@router.get("/detail/{simulation_id}", response_model=SimulationRead)
@router.get("/replay/{simulation_id}", response_model=SimulationRead)
async def get_simulation_detail(
    simulation_id: str,
    db: DbSession,
    user: CurrentUser,
) -> SimulationRead:
    """Return the exact saved output for a past simulation."""
    simulation = await _owned_simulation(simulation_id, user.id, db)
    if simulation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulation not found.",
        )
    return simulation


@router.get("/{profile_id}", response_model=list[SimulationSummary])
async def get_simulation_history(
    profile_id: str,
    db: DbSession,
    user: CurrentUser,
) -> list[SimulationSummary]:
    """List simulations, including linked scenarios, for an owned profile."""
    profile_exists = await db.scalar(
        select(UserProfile.id).where(
            UserProfile.id == profile_id,
            UserProfile.user_id == user.id,
        )
    )
    if profile_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )

    result = await db.execute(
        select(Simulation)
        .where(Simulation.profile_id == profile_id)
        .order_by(Simulation.created_at.desc(), Simulation.id.desc())
        .options(selectinload(Simulation.paths))
    )
    return [
        SimulationSummary(
            id=simulation.id,
            parent_simulation_id=simulation.parent_simulation_id,
            label=simulation.label,
            engine_version=simulation.engine_version,
            path_count=len(simulation.paths),
            created_at=simulation.created_at,
        )
        for simulation in result.scalars().all()
    ]
