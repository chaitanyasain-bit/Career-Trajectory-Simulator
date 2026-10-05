"""Bounded confidence scoring for career paths."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def skill_coverage(
    user_skills: Mapping[str, int] | Sequence[str],
    role_requirements: Sequence[dict],
) -> float:
    """Calculate weighted, proficiency-aware coverage of role requirements."""
    proficiencies = (
        dict(user_skills)
        if isinstance(user_skills, Mapping)
        else {skill: 5 for skill in user_skills}
    )
    total_weight = 0.0
    acquired_weight = 0.0
    for requirement in role_requirements:
        importance = float(requirement.get("importance", 3))
        mandatory = bool(requirement.get("mandatory", True))
        weight = importance * (2.0 if mandatory else 1.0)
        required = max(1, int(requirement.get("required_proficiency", 3)))
        proficiency = min(max(int(proficiencies.get(requirement["skill"], 0)), 0), required)
        total_weight += weight
        acquired_weight += weight * proficiency / required
    return acquired_weight / total_weight if total_weight else 0.0


def calculate_confidence(
    user_skills: Mapping[str, int] | Sequence[str],
    role_requirements: Sequence[dict],
    graph_weight: float = 1.0,
    *,
    experience_score: float | None = None,
    evidence_score: float | None = None,
) -> float:
    """Combine skill fit and transition likelihood into a score in [0, 1].

    Omitting the profile-context scores retains the original 70/30 weighting
    used by the standalone engine API.
    """
    transition = min(max(float(graph_weight), 0.0), 1.0)
    coverage = skill_coverage(user_skills, role_requirements)
    if experience_score is None and evidence_score is None:
        return min(max((coverage * 0.7) + (transition * 0.3), 0.0), 1.0)

    experience = min(max(float(experience_score or 0.0), 0.0), 1.0)
    evidence = min(max(float(evidence_score or 0.0), 0.0), 1.0)
    return min(
        max((coverage * 0.6) + (transition * 0.2) + (experience * 0.1) + (evidence * 0.1), 0.0),
        1.0,
    )


def get_confidence_label(score: float) -> str:
    """Convert a numeric confidence score to a stable display label."""
    if score >= 0.75:
        return "High"
    if score >= 0.45:
        return "Medium"
    return "Low"
