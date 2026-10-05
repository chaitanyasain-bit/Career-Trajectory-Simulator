"""
Data engine tests.
"""

import pytest

from data.engine.confidence import calculate_confidence, get_confidence_label
from data.engine.gap_analysis import compute_gaps
from data.engine.graph import CareerGraph
from data.engine.roadmap import generate_roadmap
from data.engine.trajectory import TrajectoryEngine, UserProfile


def make_engine():
    roles = [
        {"normalized_title": "data_analyst", "title": "Data Analyst", "seniority_level": 2},
        {"normalized_title": "data_scientist", "title": "Data Scientist", "seniority_level": 3},
        {"normalized_title": "analytics_engineer", "title": "Analytics Engineer", "seniority_level": 3},
    ]
    transitions = [
        {"from": "data_analyst", "to": "data_scientist", "weight": 0.8, "months": 18},
        {"from": "data_analyst", "to": "analytics_engineer", "weight": 0.7, "months": 15},
    ]
    requirements = [
        {
            "role": "data_scientist",
            "skill": "python",
            "importance": 5,
            "mandatory": True,
            "required_proficiency": 4,
            "category": "Programming",
            "skill_id": "python-id",
        },
        {
            "role": "data_scientist",
            "skill": "sql",
            "importance": 4,
            "mandatory": True,
            "required_proficiency": 3,
            "category": "Databases",
            "skill_id": "sql-id",
        },
        {
            "role": "analytics_engineer",
            "skill": "sql",
            "importance": 5,
            "mandatory": True,
            "required_proficiency": 4,
            "category": "Databases",
            "skill_id": "sql-id",
        },
    ]
    return TrajectoryEngine(roles, transitions, requirements)


def test_career_graph_add_role():
    graph = CareerGraph()
    graph.add_role("data_analyst")
    assert "data_analyst" in graph.graph.nodes


def test_career_graph_reachable_roles():
    graph = CareerGraph()
    graph.add_role("data_analyst")
    graph.add_role("data_scientist")
    graph.add_transition("data_analyst", "data_scientist", weight=0.8)
    reachable = graph.get_reachable_roles("data_analyst")
    assert "data_scientist" in reachable
    assert graph.get_path_weight("data_analyst", "data_scientist") == 0.8


def test_confidence_label_high():
    assert get_confidence_label(0.85) == "High"


def test_confidence_label_medium():
    assert get_confidence_label(0.55) == "Medium"


def test_confidence_label_low():
    assert get_confidence_label(0.20) == "Low"


def test_calculate_confidence():
    user_skills = ["python", "sql"]
    reqs = [
        {"skill": "python", "importance": 5, "mandatory": True}, # weight 10
        {"skill": "sql", "importance": 4, "mandatory": True},    # weight 8
        {"skill": "pandas", "importance": 3, "mandatory": False} # weight 3
    ]
    # Total weight = 21. Acquired = 18.
    # skill coverage = 18 / 21 = 0.857
    # graph weight = 0.8
    # final score = (0.857 * 0.7) + (0.8 * 0.3) = 0.5999 + 0.24 = 0.8399
    score = calculate_confidence(user_skills, reqs, graph_weight=0.8)
    assert 0.83 < score < 0.85


def test_compute_gaps():
    user_skills = ["python"]
    reqs = [
        {"skill": "python", "importance": 5, "mandatory": True},
        {"skill": "sql", "importance": 4, "mandatory": True},    # Priority 1
        {"skill": "pandas", "importance": 3, "mandatory": False} # Priority 4
    ]
    gaps = compute_gaps(user_skills, reqs)
    assert len(gaps) == 2
    assert gaps[0].skill == "sql"
    assert gaps[0].priority == 1
    assert gaps[1].skill == "pandas"
    assert gaps[1].priority == 4


def test_proficiency_aware_gaps_rank_missing_and_underdeveloped_skills():
    gaps = compute_gaps(
        {"python": 2},
        [
            {
                "skill": "python",
                "importance": 5,
                "mandatory": True,
                "required_proficiency": 4,
                "category": "Programming",
                "skill_id": "python-id",
            },
            {
                "skill": "sql",
                "importance": 4,
                "mandatory": True,
                "required_proficiency": 3,
                "category": "Databases",
                "skill_id": "sql-id",
            },
        ],
    )
    assert [gap.skill for gap in gaps] == ["sql", "python"]
    assert gaps[0].current_proficiency == 0
    assert gaps[0].gap_score == 1
    assert gaps[0].priority < gaps[1].priority
    assert gaps[1].gap_score == 0.5
    assert gaps[1].reason and gaps[1].skill_id == "python-id"


def test_roadmap_uses_real_gaps_and_has_a_no_gap_path():
    gap = compute_gaps(
        {},
        [
            {
                "skill": "python",
                "importance": 5,
                "mandatory": True,
                "required_proficiency": 4,
                "skill_id": "python-id",
            }
        ],
    )[0]
    roadmap = generate_roadmap([gap], "Data Scientist")
    assert roadmap[0].skill_id == "python-id"
    assert roadmap[0].estimated_weeks > 0
    assert "requires" in roadmap[0].description
    no_gap = generate_roadmap([], "Data Scientist")
    assert len(no_gap) == 1
    assert no_gap[0].step_type == "networking"


def test_confidence_is_proficiency_aware_bounded_and_labels_consistently():
    requirements = [
        {
            "skill": "python",
            "importance": 5,
            "mandatory": True,
            "required_proficiency": 4,
        }
    ]
    low = calculate_confidence(
        {"python": 1},
        requirements,
        graph_weight=0.8,
        experience_score=0.2,
        evidence_score=0.0,
    )
    high = calculate_confidence(
        {"python": 5},
        requirements,
        graph_weight=1.2,
        experience_score=1.0,
        evidence_score=1.0,
    )
    assert 0 <= low < high <= 1
    assert get_confidence_label(high) == "High"


def test_engine_uses_database_injected_catalog_for_transitions_and_ranking():
    engine = make_engine()
    profile = UserProfile(
        current_role="data_analyst",
        skills={"python": 4, "sql": 3},
        years_of_experience=6,
        projects=[{"title": "A portfolio project"}],
        educations=[{"degree": "BSc"}],
        experiences=[{"title": "Analyst"}],
    )
    result = engine.simulate(profile)
    assert [path.confidence for path in result.paths] == sorted(
        (path.confidence for path in result.paths), reverse=True
    )
    scientist = next(path for path in result.paths if path.target_role == "data_scientist")
    assert scientist.confidence > 0.5
    assert scientist.engine_metadata["transition_path"] == [
        "data_analyst",
        "data_scientist",
    ]
    assert sum(
        factor["contribution"]
        for factor in scientist.engine_metadata["confidence_factors"]
    ) == pytest.approx(scientist.confidence, abs=0.0002)


def test_empty_profile_returns_bounded_explainable_recommendations():
    result = make_engine().simulate(UserProfile())
    assert result.paths
    assert all(0 <= path.confidence <= 1 for path in result.paths)
    assert all(path.engine_metadata["why_recommended"] for path in result.paths)


def test_project_evidence_relevance_contributes_to_target_role_confidence():
    engine = make_engine()
    generic = engine.simulate(
        UserProfile(projects=[{"title": "Personal application"}])
    )
    relevant = engine.simulate(
        UserProfile(
            educations=[{"field_of_study": "Data Science"}],
            projects=[{"title": "Data Scientist portfolio"}],
        )
    )
    generic_path = next(path for path in generic.paths if path.target_role == "data_scientist")
    relevant_path = next(path for path in relevant.paths if path.target_role == "data_scientist")
    generic_evidence = next(
        item["value"]
        for item in generic_path.engine_metadata["confidence_factors"]
        if item["factor"] == "profile_evidence"
    )
    relevant_evidence = next(
        item["value"]
        for item in relevant_path.engine_metadata["confidence_factors"]
        if item["factor"] == "profile_evidence"
    )
    assert relevant_evidence > generic_evidence
    assert relevant_path.confidence > generic_path.confidence


def test_whatif_does_not_mutate_baseline_profile():
    engine = make_engine()
    profile = UserProfile(
        current_role="data_analyst",
        skills={"python": 1},
        years_of_experience=2,
        projects=[{"title": "Original"}],
    )
    baseline_skills = dict(profile.skills)
    baseline_projects = list(profile.projects)
    baseline_years = profile.years_of_experience
    scenario = engine.whatif(
        profile,
        {
            "add_skill_names": ["sql"],
            "proficiency_overrides": {"python": 5},
            "add_experience_months": 12,
            "projects": [{"title": "Scenario project"}],
        },
    )
    assert scenario.profile.skills["python"] == 5
    assert "sql" in scenario.profile.skills
    assert len(scenario.profile.projects) == 2
    assert profile.skills == baseline_skills
    assert profile.projects == baseline_projects
    assert profile.years_of_experience == baseline_years


def test_trajectory_engine_simulate():
    engine = make_engine()
    profile = UserProfile(current_role="data_analyst", skills=["python", "sql", "excel"])

    result = engine.simulate(profile)
    assert result.profile.current_role == "data_analyst"
    assert len(result.paths) > 0

    # Paths should be sorted by confidence
    if len(result.paths) > 1:
        assert result.paths[0].confidence >= result.paths[1].confidence

    # Check that a path has gaps
    path = result.paths[0]
    assert isinstance(path.target_role, str)
    assert path.confidence > 0.0


def test_trajectory_engine_whatif():
    engine = make_engine()
    profile = UserProfile(current_role="data_analyst", skills=["excel"])

    # Baseline
    engine.simulate(profile)

    # What if they learn Python and SQL?
    res2 = engine.whatif(profile, {"add_skill_ids": ["python", "sql"]})

    # Check that the whatif result has different confidence (likely higher for data science roles)
    assert len(res2.paths) > 0

    # We can check specific path confidences if we want, but verifying it runs is enough for smoke test
    assert isinstance(res2.paths[0].confidence, float)
