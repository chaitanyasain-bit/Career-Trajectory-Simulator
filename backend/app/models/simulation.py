"""
Simulation, SimulationPath, SkillGap, and Roadmap models.

Design:
- Simulation = one run of the trajectory engine for a profile snapshot.
- SimulationPath = one candidate career path output from that run.
- SkillGap = per-path gap analysis result.
- RoadmapStep = ordered action items for a specific path.
- ConfidenceMetadata = stores explanation/evidence for the confidence score
  so the UI can render "why" explanations.

JSONB approach for metadata: SimulationPath.engine_metadata stores the
raw engine output dict, giving flexibility while structured columns capture
the queryable fields.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, new_uuid


class Simulation(Base, TimestampMixin):
    """
    One full trajectory simulation run.

    profile_snapshot: JSON snapshot of the user's profile at the time
    of simulation — important so historical simulations remain accurate
    even as the profile changes.
    engine_version: tracks which version of the engine produced the result.
    """

    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False
    )
    parent_simulation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("simulations.id", ondelete="SET NULL"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)  # user-given name
    engine_version: Mapped[str] = mapped_column(String(20), default="0.1.0", nullable=False)
    profile_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)   # frozen copy of input
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    profile: Mapped[UserProfile] = relationship("UserProfile", back_populates="simulations")
    parent_simulation: Mapped[Simulation | None] = relationship(
        "Simulation",
        remote_side="Simulation.id",
        back_populates="what_if_simulations",
    )
    what_if_simulations: Mapped[list[Simulation]] = relationship(
        "Simulation",
        back_populates="parent_simulation",
        cascade="save-update, merge",
    )
    paths: Mapped[list[SimulationPath]] = relationship(
        "SimulationPath", back_populates="simulation", cascade="all, delete-orphan",
        order_by="SimulationPath.rank",
    )

    __table_args__ = (
        Index("ix_simulations_profile_id", "profile_id"),
        Index("ix_simulations_parent_simulation_id", "parent_simulation_id"),
    )

    def __repr__(self) -> str:
        return f"<Simulation id={self.id!r} profile={self.profile_id!r}>"


class SimulationPath(Base, TimestampMixin):
    """
    One candidate career path within a simulation.

    confidence_score: 0.0–1.0 output of the scoring model.
    confidence_label: "High" / "Medium" / "Low" derived category.
    estimated_months: engine estimate of time to reach target_role.
    engine_metadata: arbitrary JSON from the engine (feature vector, etc.)
    """

    __tablename__ = "simulation_paths"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    simulation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False
    )
    target_role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_label: Mapped[str] = mapped_column(String(10), nullable=False)  # High/Medium/Low
    estimated_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)   # 1 = best match
    engine_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    simulation: Mapped[Simulation] = relationship("Simulation", back_populates="paths")
    target_role: Mapped[Role] = relationship("Role")
    skill_gaps: Mapped[list[SkillGap]] = relationship(
        "SkillGap", back_populates="simulation_path", cascade="all, delete-orphan"
    )
    roadmap_steps: Mapped[list[RoadmapStep]] = relationship(
        "RoadmapStep", back_populates="simulation_path", cascade="all, delete-orphan",
        order_by="RoadmapStep.step_order",
    )

    __table_args__ = (
        CheckConstraint(
            "confidence_score BETWEEN 0.0 AND 1.0", name="ck_sim_path_confidence"
        ),
        CheckConstraint(
            "confidence_label IN ('High', 'Medium', 'Low')", name="ck_sim_path_label"
        ),
        Index("ix_sim_paths_simulation_id", "simulation_id"),
        Index("ix_sim_paths_target_role_id", "target_role_id"),
        Index("ix_sim_paths_confidence", "confidence_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<SimulationPath sim={self.simulation_id!r} "
            f"role={self.target_role_id!r} conf={self.confidence_score:.2f}>"
        )


class SkillGap(Base, TimestampMixin):
    """
    A single skill gap identified for a SimulationPath.

    priority_rank: 1 = learn this first (highest impact on closing gap).
    gap_score: estimated magnitude of the gap [0.0–1.0].
    learning_resource: optional curated URL/course suggestion.
    """

    __tablename__ = "skill_gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    simulation_path_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("simulation_paths.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    gap_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 1.0 = fully missing
    current_proficiency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    required_proficiency: Mapped[int | None] = mapped_column(Integer, nullable=True)
    importance_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_mandatory: Mapped[bool | None] = mapped_column(nullable=True)
    learning_resource: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    simulation_path: Mapped[SimulationPath] = relationship(
        "SimulationPath", back_populates="skill_gaps"
    )
    skill: Mapped[Skill] = relationship("Skill")

    __table_args__ = (
        CheckConstraint("gap_score BETWEEN 0.0 AND 1.0", name="ck_skill_gap_score"),
        Index("ix_skill_gaps_sim_path_id", "simulation_path_id"),
        Index("ix_skill_gaps_skill_id", "skill_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<SkillGap path={self.simulation_path_id!r} "
            f"skill={self.skill_id!r} rank={self.priority_rank}>"
        )


class RoadmapStep(Base, TimestampMixin):
    """
    One concrete action item in a career roadmap for a SimulationPath.

    step_order: 1-indexed ordering (1 = do first).
    step_type: "skill" | "project" | "certification" | "networking" | "experience"
    estimated_weeks: engine estimate for completing this step.
    resource_url: optional curated link (course, book, tool, etc.)
    """

    __tablename__ = "roadmap_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    simulation_path_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("simulation_paths.id", ondelete="CASCADE"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_type: Mapped[str] = mapped_column(String(50), default="skill", nullable=False)
    estimated_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resource_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    skill_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )  # link back to the specific skill being built

    # ── Relationships ─────────────────────────────────────────────────────────
    simulation_path: Mapped[SimulationPath] = relationship(
        "SimulationPath", back_populates="roadmap_steps"
    )
    skill: Mapped[Skill | None] = relationship("Skill")

    __table_args__ = (
        CheckConstraint(
            "step_type IN ('skill', 'project', 'certification', 'networking', 'experience')",
            name="ck_roadmap_step_type",
        ),
        Index("ix_roadmap_steps_sim_path_id", "simulation_path_id"),
    )

    def __repr__(self) -> str:
        return f"<RoadmapStep order={self.step_order} title={self.title!r}>"


# Circular import resolution
from app.models.profile import UserProfile  # noqa: E402, F401
from app.models.role import Role  # noqa: E402, F401
from app.models.skill import Skill  # noqa: E402, F401
