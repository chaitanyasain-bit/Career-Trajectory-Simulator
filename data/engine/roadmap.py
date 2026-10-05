"""Turn skill gaps into ordered, actionable roadmap steps."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil

from data.engine.gap_analysis import SkillGap


@dataclass
class EngineRoadmapStep:
    title: str
    description: str
    step_type: str
    estimated_weeks: int
    skill: str | None = None
    skill_id: str | None = None
    resource_url: str | None = None


_RESOURCES = {
    "python": "https://docs.python.org/3/tutorial/",
    "sql": "https://www.postgresql.org/docs/current/tutorial.html",
    "pandas": "https://pandas.pydata.org/docs/getting_started/intro_tutorials/",
    "numpy": "https://numpy.org/learn/",
    "scikit_learn": "https://scikit-learn.org/stable/getting_started.html",
    "pytorch": "https://pytorch.org/tutorials/",
    "aws": "https://skillbuilder.aws/",
    "gcp": "https://cloud.google.com/learn/training",
    "azure": "https://learn.microsoft.com/training/azure/",
    "docker": "https://docs.docker.com/get-started/",
}


def generate_roadmap(
    skill_gaps: Sequence[SkillGap],
    target_role: str,
) -> list[EngineRoadmapStep]:
    """Generate ordered learning, practice, and readiness steps."""
    if not skill_gaps:
        return [
            EngineRoadmapStep(
                title="Prepare for target-role interviews",
                description=(
                    f"Your listed skills meet the catalog requirements for {target_role}. "
                    "Validate your readiness with role-specific interview practice and a "
                    "portfolio review."
                ),
                step_type="networking",
                estimated_weeks=2,
            )
        ]

    ordered_gaps = sorted(
        skill_gaps,
        key=lambda gap: (
            0 if gap.is_mandatory else 1,
            -gap.importance_level,
            -gap.gap_score,
            gap.skill,
        ),
    )
    steps: list[EngineRoadmapStep] = []
    for gap in ordered_gaps:
        name = gap.skill.replace("_", " ").title()
        missing = gap.current_proficiency == 0
        steps.append(
            EngineRoadmapStep(
                title=f"{'Learn' if missing else 'Advance'} {name}",
                description=(
                    f"{gap.reason} Complete a focused learning module and practice "
                    "the skill in a small applied exercise."
                ),
                step_type="skill",
                estimated_weeks=max(
                    1,
                    ceil(gap.gap_score * (2 + gap.importance_level)),
                ),
                skill=gap.skill,
                skill_id=gap.skill_id,
                resource_url=_RESOURCES.get(gap.skill),
            )
        )

    high_priority_skills = [
        gap.skill.replace("_", " ").title()
        for gap in ordered_gaps
        if gap.is_mandatory and gap.importance_level >= 4
    ][:4]
    if high_priority_skills:
        steps.append(
            EngineRoadmapStep(
                title="Apply core skills in a portfolio project",
                description=(
                    "Build and document a project applying "
                    + ", ".join(high_priority_skills)
                    + f" to a realistic {target_role} problem."
                ),
                step_type="project",
                estimated_weeks=3,
            )
        )

    steps.append(
        EngineRoadmapStep(
            title="Review portfolio and practice interviews",
            description=(
                f"Map project outcomes to {target_role} responsibilities, update your "
                "resume, and practice technical and behavioral interviews."
            ),
            step_type="networking",
            estimated_weeks=2,
        )
    )
    return steps
