"""Skill-gap analysis for catalog-backed role requirements."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass
class SkillGap:
    skill: str
    priority: int
    category: str
    importance_level: int = 3
    is_mandatory: bool = True
    current_proficiency: int = 0
    required_proficiency: int = 3
    gap_score: float = 1.0
    reason: str = ""
    skill_id: str | None = None


def compute_gaps(
    user_skills: Mapping[str, int] | Sequence[str],
    role_requirements: Sequence[dict],
) -> list[SkillGap]:
    """Return missing and underdeveloped skills ordered by learning impact."""
    proficiencies = (
        dict(user_skills)
        if isinstance(user_skills, Mapping)
        else {skill: 5 for skill in user_skills}
    )
    gaps: list[SkillGap] = []
    for requirement in role_requirements:
        skill = requirement["skill"]
        required = int(requirement.get("required_proficiency", 3))
        current = int(proficiencies.get(skill, 0))
        if current >= required:
            continue

        importance = int(requirement.get("importance", 3))
        mandatory = bool(requirement.get("mandatory", True))
        gap_score = round((required - current) / required, 4)
        if mandatory and importance >= 4:
            priority = 1 if current == 0 else 2
        elif mandatory:
            priority = 2 if current == 0 else 3
        elif importance >= 4:
            priority = 3 if current == 0 else 4
        else:
            priority = 4 if current == 0 else 5
        presence = (
            "not yet listed on the profile"
            if current == 0
            else f"currently at proficiency {current}/5"
        )
        gaps.append(
            SkillGap(
                skill=skill,
                priority=priority,
                category=requirement.get("category", "Other"),
                importance_level=importance,
                is_mandatory=mandatory,
                current_proficiency=current,
                required_proficiency=required,
                gap_score=gap_score,
                reason=(
                    f"{presence}; this role requires {required}/5 proficiency "
                    f"and assigns importance {importance}/5"
                    + (" (mandatory)." if mandatory else ".")
                ),
                skill_id=requirement.get("skill_id"),
            )
        )

    return sorted(
        gaps,
        key=lambda gap: (
            gap.priority,
            0 if gap.is_mandatory else 1,
            -gap.importance_level,
            -gap.gap_score,
            gap.skill,
        ),
    )
