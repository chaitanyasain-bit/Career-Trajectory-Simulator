"""Catalog-driven career trajectory and scenario simulation engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import ceil
from typing import Any

import networkx as nx

from data.engine.confidence import (
    calculate_confidence,
    get_confidence_label,
    skill_coverage,
)
from data.engine.gap_analysis import SkillGap as EngineSkillGap
from data.engine.gap_analysis import compute_gaps
from data.engine.graph import CareerGraph, build_career_graph

ENGINE_VERSION = "2.0.0"


@dataclass
class UserProfile:
    """Immutable simulation input assembled from a persisted profile snapshot."""

    current_role: str | None = None
    skills: dict[str, int] | list[str] = field(default_factory=dict)
    skill_experience_months: dict[str, int | None] = field(default_factory=dict)
    years_of_experience: float = 0.0
    projects: list[dict[str, Any]] = field(default_factory=list)
    educations: list[dict[str, Any]] = field(default_factory=list)
    experiences: list[dict[str, Any]] = field(default_factory=list)
    bio: str | None = None
    location: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.skills, dict):
            self.skills = {skill: 5 for skill in self.skills}


@dataclass
class CareerPath:
    target_role: str
    confidence: float
    confidence_label: str
    skill_gaps: list[EngineSkillGap] = field(default_factory=list)
    estimated_months: int = 0
    engine_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    profile: UserProfile
    paths: list[CareerPath] = field(default_factory=list)


def _profile_role_relevance(profile: UserProfile, role: dict[str, Any]) -> float:
    target_terms = {
        token
        for value in (role.get("title", ""), role.get("domain", ""))
        for token in re.findall(r"[a-z]+", str(value).lower())
        if token not in {"senior", "junior", "lead", "principal", "staff"}
    }
    if not target_terms:
        return 0.0
    evidence_values = [profile.bio or ""]
    for entries in (profile.experiences, profile.educations, profile.projects):
        evidence_values.extend(
            str(value)
            for entry in entries
            for value in entry.values()
            if value is not None
        )
    evidence_terms = {
        token
        for value in evidence_values
        for token in re.findall(r"[a-z]+", value.lower())
    }
    return len(target_terms & evidence_terms) / len(target_terms)


class TrajectoryEngine:
    """Simulate ranked roles from an injected, versionable career catalog."""

    def __init__(
        self,
        roles: list[dict[str, Any]],
        transitions: list[dict[str, Any]],
        requirements: list[dict[str, Any]],
        *,
        max_hops: int = 2,
        max_paths: int = 10,
    ) -> None:
        self.roles = {role["normalized_title"]: role for role in roles}
        graph_roles = [
            {
                "normalized_title": role["normalized_title"],
                "title": role["title"],
                "seniority_level": role.get("seniority_level", 2),
            }
            for role in roles
        ]
        self.graph: CareerGraph = build_career_graph(graph_roles, transitions)
        self.transitions = transitions
        self.max_hops = max_hops
        self.max_paths = max_paths
        self.requirements_map: dict[str, list[dict[str, Any]]] = {}
        for requirement in requirements:
            self.requirements_map.setdefault(requirement["role"], []).append(requirement)

    def simulate(self, profile: UserProfile) -> SimulationResult:
        if profile.current_role in self.roles:
            candidates = self.graph.get_reachable_roles(profile.current_role, self.max_hops)
            if not candidates:
                candidates = [role for role in self.roles if role != profile.current_role]
        else:
            candidates = list(self.roles)

        paths: list[CareerPath] = []
        for role_name in candidates:
            role = self.roles[role_name]
            requirements = self.requirements_map.get(role_name, [])
            gaps = compute_gaps(profile.skills, requirements)
            coverage = skill_coverage(profile.skills, requirements)
            route = self._transition_route(profile.current_role, role_name)
            graph_weight = route["weight"] if route else 0.35
            experience_score = min(
                max(profile.years_of_experience / max(role.get("seniority_level", 2) * 2, 2), 0),
                1,
            )
            reported_skill_months = [
                min(months / 24, 1.0)
                for name, months in profile.skill_experience_months.items()
                if name in profile.skills and months is not None
            ]
            skill_evidence = (
                sum(reported_skill_months) / len(reported_skill_months)
                if reported_skill_months
                else 0.0
            )
            evidence_score = min(
                1.0,
                (len(profile.experiences) * 0.3)
                + (len(profile.educations) * 0.2)
                + (len(profile.projects) * 0.35)
                + (skill_evidence * 0.15),
            )
            role_relevance = _profile_role_relevance(profile, role)
            evidence_score *= 0.75 + (0.25 * role_relevance)
            confidence = calculate_confidence(
                profile.skills,
                requirements,
                graph_weight,
                experience_score=experience_score,
                evidence_score=evidence_score,
            )
            gap_months = sum(gap.gap_score * 4 for gap in gaps)
            route_months = route["months"] if route else 0
            estimated_months = max(
                1,
                ceil(route_months + gap_months)
                if route_months or gap_months
                else ceil(float(role.get("avg_years_to_reach") or 1) * 12),
            )
            factor_values = [
                {
                    "factor": "skill_match",
                    "weight": 0.6,
                    "value": round(coverage, 4),
                    "contribution": round(coverage * 0.6, 4),
                    "explanation": (
                        f"Proficiency-adjusted coverage of {len(requirements)} role skill "
                        f"requirements is {coverage:.0%}."
                    ),
                },
                {
                    "factor": "career_transition",
                    "weight": 0.2,
                    "value": round(graph_weight, 4),
                    "contribution": round(graph_weight * 0.2, 4),
                    "explanation": (
                        "Based on the product of transition weights along the shortest "
                        "catalog path."
                        if route
                        else "No transition path is available; a conservative neutral prior is used."
                    ),
                },
                {
                    "factor": "experience",
                    "weight": 0.1,
                    "value": round(experience_score, 4),
                    "contribution": round(experience_score * 0.1, 4),
                    "explanation": (
                        f"{profile.years_of_experience:g} years of experience compared with "
                        f"the target role's seniority level {role.get('seniority_level', 2)}."
                    ),
                },
                {
                    "factor": "profile_evidence",
                    "weight": 0.1,
                    "value": round(evidence_score, 4),
                    "contribution": round(evidence_score * 0.1, 4),
                    "explanation": (
                        f"Evidence includes {len(profile.experiences)} work entries, "
                        f"{len(profile.educations)} education entries, and "
                        f"{len(profile.projects)} projects, and "
                        f"{len(reported_skill_months)} skills with reported practice history; "
                        f"{role_relevance:.0%} of target-role terms appear in the profile evidence."
                    ),
                },
            ]
            metadata = {
                "target_role_title": role["title"],
                "target_role_domain": role.get("domain"),
                "target_seniority_level": role.get("seniority_level", 2),
                "confidence_factors": factor_values,
                "why_recommended": [
                    item["explanation"]
                    for item in factor_values
                    if item["value"] > 0
                ],
                "transition_path": route["roles"] if route else [],
                "gap_count": len(gaps),
                "profile_completeness": round(evidence_score, 4),
                "required_skill_count": len(requirements),
            }
            paths.append(
                CareerPath(
                    target_role=role_name,
                    confidence=confidence,
                    confidence_label=get_confidence_label(confidence),
                    skill_gaps=gaps,
                    estimated_months=estimated_months,
                    engine_metadata=metadata,
                )
            )

        paths.sort(key=lambda path: (-path.confidence, path.target_role))
        return SimulationResult(profile=profile, paths=paths[: self.max_paths])

    def _transition_route(
        self,
        current_role: str | None,
        target_role: str,
    ) -> dict[str, Any] | None:
        if not current_role or current_role == target_role or not (
            current_role in self.graph.graph and target_role in self.graph.graph
        ):
            return None
        try:
            role_path = nx.shortest_path(self.graph.graph, current_role, target_role)
        except nx.NetworkXNoPath:
            return None
        weight = 1.0
        months = 0
        for source, target in zip(role_path, role_path[1:], strict=False):
            edge = self.graph.graph[source][target]
            weight *= float(edge.get("weight", 0.5))
            months += int(edge.get("months", 12))
        return {"roles": role_path, "weight": weight, "months": months}

    def whatif(self, profile: UserProfile, hypothetical_change: dict) -> SimulationResult:
        """Run a non-mutating scenario against a copied profile."""
        skills = dict(profile.skills)
        for skill_name in hypothetical_change.get(
            "add_skill_names",
            hypothetical_change.get("add_skill_ids", []),
        ):
            skills.setdefault(skill_name, 3)
        skills.update(hypothetical_change.get("proficiency_overrides", {}))
        added_projects = hypothetical_change.get("projects", [])
        scenario = UserProfile(
            current_role=profile.current_role,
            skills=skills,
            skill_experience_months=dict(profile.skill_experience_months),
            years_of_experience=profile.years_of_experience
            + (hypothetical_change.get("add_experience_months", 0) / 12),
            projects=[*profile.projects, *added_projects],
            educations=list(profile.educations),
            experiences=list(profile.experiences),
            bio=profile.bio,
            location=profile.location,
        )
        return self.simulate(scenario)
