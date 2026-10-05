"""API contract tests using the isolated seeded test database."""

from __future__ import annotations

import uuid

from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app
from app.models import Role, Skill
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


def _run_async(callback):
    import asyncio
    import inspect

    awaitable = callback if inspect.isawaitable(callback) else callback()
    return asyncio.run(awaitable)


async def _initialize_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        await seed_database(session)


async def _drop_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def setup_module():
    _run_async(_initialize_database)


def teardown_module():
    _run_async(_drop_database)
    app.dependency_overrides.clear()


client = TestClient(app)


def register_account(email: str | None = None) -> tuple[dict[str, str], str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email or f"{uuid.uuid4()}@example.com",
            "password": "correct-horse-battery-staple",
            "full_name": "  Test User  ",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["full_name"] == "Test User"
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"]["email"]


def catalog_ids() -> tuple[str, str]:
    async def query_ids():
        async with TestingSessionLocal() as session:
            role_id = await session.scalar(select(Role.id).where(Role.normalized_title == "data_analyst"))
            skill_id = await session.scalar(select(Skill.id).where(Skill.normalized_name == "python"))
            return role_id, skill_id

    import asyncio

    return asyncio.run(query_ids())


def catalog_skill_id(normalized_name: str) -> str:
    async def query_id():
        async with TestingSessionLocal() as session:
            return await session.scalar(
                select(Skill.id).where(Skill.normalized_name == normalized_name)
            )

    import asyncio

    skill_id = asyncio.run(query_id())
    assert skill_id is not None
    return skill_id


def create_profile(headers: dict[str, str], **overrides):
    role_id, skill_id = catalog_ids()
    payload = {
        "current_role_id": role_id,
        "years_of_experience": 5.0,
        "bio": "Test bio",
        "skills": [{"skill_id": skill_id, "proficiency_level": 4, "months_of_experience": 24}],
        "educations": [
            {
                "institution": "Example University",
                "degree": "BSc",
                "field_of_study": "Computer Science",
                "start_year": 2015,
                "end_year": 2019,
            }
        ],
        "experiences": [
            {
                "title": "Analyst",
                "company": "Example Co",
                "start_date": "2020-01",
                "is_current": True,
            }
        ],
        "projects": [
            {
                "title": "Forecasting project",
                "description": "Built a forecasting model.",
                "start_date": "2023-01",
                "is_current": True,
            }
        ],
    }
    payload.update(overrides)
    return client.post("/api/v1/profiles/me", json=payload, headers=headers)


def test_registration_login_and_current_account():
    email = f"{uuid.uuid4()}@example.com"
    headers, normalized_email = register_account(email.upper())

    current = client.get("/api/v1/auth/me", headers=headers)
    assert current.status_code == 200
    assert current.json()["email"] == normalized_email
    assert "hashed_password" not in current.json()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-staple"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    ).status_code == 200


def test_registration_rejects_duplicate_email_and_invalid_input():
    email = f"{uuid.uuid4()}@example.com"
    register_account(email)

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": email.upper(),
            "password": "correct-horse-battery-staple",
            "full_name": "Duplicate User",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    invalid = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short", "full_name": ""},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_rejects_bad_password_without_disclosing_account():
    headers, email = register_account()
    del headers

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password."


def test_authentication_rejects_missing_invalid_and_tampered_tokens():
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    ).status_code == 401
    headers, _ = register_account()
    token = headers["Authorization"].removeprefix("Bearer ")
    token = token[:-1] + ("a" if token[-1] != "a" else "b")
    tampered = token
    headers["Authorization"] = "Bearer " + token
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert response.status_code == 401


def test_profile_creation_read_update_and_validation():
    headers, _ = register_account()
    created = create_profile(headers)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data["user_id"]
    assert len(data["user_skills"]) == 1
    assert len(data["educations"]) == 1
    assert len(data["experiences"]) == 1
    assert len(data["projects"]) == 1

    fetched = client.get("/api/v1/profiles/me", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == data["id"]

    update = client.patch(
        "/api/v1/profiles/me",
        json={"bio": "Updated bio", "years_of_experience": 6.5},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["bio"] == "Updated bio"
    assert len(update.json()["projects"]) == 1
    assert len(update.json()["experiences"]) == 1

    duplicate = create_profile(headers)
    assert duplicate.status_code == 409

    invalid_role = client.patch(
        "/api/v1/profiles/me",
        json={"current_role_id": str(uuid.uuid4())},
        headers=headers,
    )
    assert invalid_role.status_code == 422

    invalid_skill = client.patch(
        "/api/v1/profiles/me",
        json={"skills": [{"skill_id": str(uuid.uuid4()), "proficiency_level": 3}]},
        headers=headers,
    )
    assert invalid_skill.status_code == 422


def test_profile_access_requires_auth_and_is_account_scoped():
    first_headers, _ = register_account()
    second_headers, _ = register_account()
    created = create_profile(first_headers)
    assert created.status_code == 201

    assert client.get("/api/v1/profiles/me").status_code == 401
    assert client.get("/api/v1/profiles/me", headers=second_headers).status_code == 404
    assert client.patch(
        "/api/v1/profiles/me",
        json={"bio": "unauthorized"},
        headers=second_headers,
    ).status_code == 404


def test_profile_rejects_invalid_nested_values():
    headers, _ = register_account()
    invalid = create_profile(
        headers,
        years_of_experience=61,
        experiences=[
            {"title": "Invalid dates", "start_date": "2024-13", "end_date": "2023-01"}
        ],
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    duplicate_skills = create_profile(
        headers,
        skills=[
            {"skill_id": catalog_ids()[1]},
            {"skill_id": catalog_ids()[1]},
        ],
    )
    assert duplicate_skills.status_code == 422


def test_role_detail_includes_skill_requirements_for_frontend():
    role_id, _ = catalog_ids()

    response = client.get(f"/api/v1/roles/{role_id}")

    assert response.status_code == 200, response.text
    requirements = response.json()["skill_requirements"]
    assert requirements
    assert all(1 <= item["required_proficiency"] <= 5 for item in requirements)
    assert all(item["skill"] and item["skill"]["name"] for item in requirements)


def test_simulation_rejects_unauthenticated_and_cross_account_profile_access():
    headers, _ = register_account()
    profile = create_profile(headers).json()
    unauthenticated = client.post(
        f"/api/v1/simulate/{profile['id']}",
        json={"label": "Test"},
    )
    assert unauthenticated.status_code == 401

    other_headers, _ = register_account()
    forbidden_profile = client.post(
        f"/api/v1/simulate/{profile['id']}",
        json={"label": "Test"},
        headers=other_headers,
    )
    assert forbidden_profile.status_code == 404


def test_history_and_roadmap_are_account_scoped():
    headers, _ = register_account()
    profile = create_profile(headers).json()
    simulation = client.post(
        f"/api/v1/simulate/{profile['id']}",
        json={"label": "Owned simulation"},
        headers=headers,
    )
    assert simulation.status_code == 201, simulation.text
    simulation_id = simulation.json()["id"]

    history = client.get(f"/api/v1/history/{profile['id']}", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["id"] == simulation_id
    detail = client.get(f"/api/v1/history/detail/{simulation_id}", headers=headers)
    assert detail.status_code == 200

    other_headers, _ = register_account()
    assert client.get(
        f"/api/v1/history/{profile['id']}", headers=other_headers
    ).status_code == 404
    assert client.get(
        f"/api/v1/history/detail/{simulation_id}", headers=other_headers
    ).status_code == 404
    assert client.post(
        f"/api/v1/simulate/{simulation_id}/whatif",
        json={"add_skill_ids": []},
        headers=other_headers,
    ).status_code == 404
    path_id = simulation.json()["paths"][0]["id"]
    assert client.get(
        f"/api/v1/roadmap/{path_id}", headers=other_headers
    ).status_code == 404


def test_simulation_saves_explanations_gaps_roadmaps_and_replayable_history():
    headers, _ = register_account()
    profile = create_profile(headers).json()
    response = client.post(
        f"/api/v1/simulate/{profile['id']}",
        json={"label": "Baseline"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    original = response.json()
    assert original["paths"]
    assert original["paths"] == sorted(
        original["paths"], key=lambda path: path["rank"]
    )
    path = original["paths"][0]
    assert 0 <= path["confidence_score"] <= 1
    assert path["engine_metadata"]["confidence_factors"]
    assert path["engine_metadata"]["why_recommended"]
    assert path["engine_metadata"]["transition_path"]
    assert path["skill_gaps"]
    assert all(gap["skill_id"] and gap["notes"] for gap in path["skill_gaps"])
    assert all(
        gap["gap_score"] > 0
        and gap["required_proficiency"] is not None
        and gap["current_proficiency"] < gap["required_proficiency"]
        for gap in path["skill_gaps"]
    )
    roadmap = path["roadmap_steps"]
    assert roadmap
    assert [step["step_order"] for step in roadmap] == list(range(1, len(roadmap) + 1))
    stored_roadmap = client.get(
        f"/api/v1/roadmap/{path['id']}", headers=headers
    )
    assert stored_roadmap.status_code == 200
    assert stored_roadmap.json() == roadmap

    replay = client.get(
        f"/api/v1/history/replay/{original['id']}", headers=headers
    )
    assert replay.status_code == 200
    assert replay.json()["paths"] == original["paths"]
    history = client.get(
        f"/api/v1/history/{profile['id']}", headers=headers
    )
    assert history.status_code == 200
    assert history.json()[0]["id"] == original["id"]
    assert history.json()[0]["path_count"] == len(original["paths"])

    async def inspect_snapshot():
        async with TestingSessionLocal() as session:
            from app.models import Simulation

            simulation = await session.get(Simulation, original["id"])
            return simulation.profile_snapshot

    snapshot = _run_async(inspect_snapshot())
    assert snapshot["profile"]["current_role"]["normalized_title"] == "data_analyst"
    assert snapshot["engine_input"]["skills"][0]["proficiency_level"] == 4
    assert snapshot["catalog_snapshot"]["transitions"]
    assert snapshot["engine_output"][0]["target_role_title"]

    async def rename_catalog_for_replay():
        async with TestingSessionLocal() as session:
            role = await session.get(Role, path["target_role_id"])
            skill = await session.get(Skill, path["skill_gaps"][0]["skill_id"])
            original_names = (role.title, skill.name)
            role.title = f"{role.title} (updated catalog)"
            skill.name = f"{skill.name} (updated catalog)"
            await session.commit()
            return original_names

    role_name, skill_name = _run_async(rename_catalog_for_replay())
    try:
        frozen_replay = client.get(
            f"/api/v1/history/replay/{original['id']}",
            headers=headers,
        )
        assert frozen_replay.status_code == 200
        replayed_path = frozen_replay.json()["paths"][0]
        assert replayed_path["target_role"]["title"] == role_name
        assert replayed_path["skill_gaps"][0]["skill"]["name"] == skill_name
    finally:
        async def restore_catalog():
            async with TestingSessionLocal() as session:
                role = await session.get(Role, path["target_role_id"])
                skill = await session.get(Skill, path["skill_gaps"][0]["skill_id"])
                role.title = role_name
                skill.name = skill_name
                await session.commit()

        _run_async(restore_catalog())


def test_whatif_is_linked_compared_and_does_not_change_profile_or_baseline():
    headers, _ = register_account()
    profile_response = create_profile(headers)
    profile = profile_response.json()
    baseline_response = client.post(
        f"/api/v1/simulate/{profile['id']}",
        json={"label": "Baseline"},
        headers=headers,
    )
    assert baseline_response.status_code == 201, baseline_response.text
    baseline = baseline_response.json()

    async def get_baseline_snapshot():
        async with TestingSessionLocal() as session:
            from app.models import Simulation

            simulation = await session.get(Simulation, baseline["id"])
            return simulation.profile_snapshot

    original_snapshot = _run_async(get_baseline_snapshot())
    scenario_response = client.post(
        f"/api/v1/simulate/{baseline['id']}/whatif",
        headers=headers,
        json={
            "add_skill_ids": [catalog_skill_id("sql")],
            "add_proficiency_overrides": {
                catalog_skill_id("python"): 5,
            },
            "add_experience_months": 12,
            "add_projects": [
                {
                    "title": "Scenario-only project",
                    "description": "A hypothetical project",
                    "start_date": "2026-01",
                }
            ],
            "label": "What-If: stronger analytics profile",
        },
    )
    assert scenario_response.status_code == 201, scenario_response.text
    scenario = scenario_response.json()
    hypothetical = scenario["hypothetical_simulation"]
    assert hypothetical["parent_simulation_id"] == baseline["id"]
    assert hypothetical["id"] != baseline["id"]
    assert scenario["confidence_changes"]
    assert scenario["improved_confidence_roles"]
    assert any(change["delta"] > 0 for change in scenario["confidence_changes"])
    assert scenario["skill_gap_changes"]
    assert any(
        change["resolved"] or change["improved"]
        for change in scenario["skill_gap_changes"]
    )
    assert scenario["roadmap_changes"]
    assert any(change["removed_steps"] for change in scenario["roadmap_changes"])

    unchanged_profile = client.get("/api/v1/profiles/me", headers=headers).json()
    assert unchanged_profile["years_of_experience"] == profile["years_of_experience"]
    assert len(unchanged_profile["user_skills"]) == len(profile["user_skills"])
    assert len(unchanged_profile["projects"]) == len(profile["projects"])

    baseline_replay = client.get(
        f"/api/v1/history/detail/{baseline['id']}",
        headers=headers,
    )
    assert baseline_replay.status_code == 200
    assert baseline_replay.json()["paths"] == baseline["paths"]

    async def inspect_scenario_records():
        async with TestingSessionLocal() as session:
            from app.models import Simulation

            saved_baseline = await session.get(Simulation, baseline["id"])
            saved_scenario = await session.get(Simulation, hypothetical["id"])
            return (
                saved_baseline.profile_snapshot,
                saved_scenario.parent_simulation_id,
                saved_scenario.profile_snapshot,
            )

    saved_snapshot, parent_id, scenario_snapshot = _run_async(inspect_scenario_records())
    assert parent_id == baseline["id"]
    assert saved_snapshot == original_snapshot
    assert scenario_snapshot["scenario_changes"]["add_experience_months"] == 12
    assert len(scenario_snapshot["profile"]["skills"]) == 2
    assert len(scenario_snapshot["profile"]["projects"]) == 2

    history = client.get(f"/api/v1/history/{profile['id']}", headers=headers).json()
    assert {row["id"] for row in history} >= {baseline["id"], hypothetical["id"]}
    assert next(row for row in history if row["id"] == hypothetical["id"])[
        "parent_simulation_id"
    ] == baseline["id"]


def test_whatif_rejects_invalid_skill_ids_and_proficiency_targets():
    headers, _ = register_account()
    profile = create_profile(headers).json()
    baseline = client.post(
        f"/api/v1/simulate/{profile['id']}",
        json={},
        headers=headers,
    ).json()
    invalid_skill = client.post(
        f"/api/v1/simulate/{baseline['id']}/whatif",
        json={"add_skill_ids": [str(uuid.uuid4())]},
        headers=headers,
    )
    assert invalid_skill.status_code == 422
    assert invalid_skill.json()["error"]["code"] == "VALIDATION_ERROR"

    invalid_override = client.post(
        f"/api/v1/simulate/{baseline['id']}/whatif",
        json={"add_proficiency_overrides": {str(uuid.uuid4()): 4}},
        headers=headers,
    )
    assert invalid_override.status_code == 422
    assert invalid_override.json()["error"]["code"] == "VALIDATION_ERROR"

    invalid_level = client.post(
        f"/api/v1/simulate/{baseline['id']}/whatif",
        json={"add_proficiency_overrides": {catalog_skill_id("python"): 6}},
        headers=headers,
    )
    assert invalid_level.status_code == 422


def test_incomplete_profile_simulates_and_recommends_with_conservative_scores():
    headers, _ = register_account()
    created = client.post(
        "/api/v1/profiles/me",
        json={"years_of_experience": 0, "skills": [], "educations": [], "projects": []},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    result = client.post(
        f"/api/v1/simulate/{created.json()['id']}",
        json={},
        headers=headers,
    )
    assert result.status_code == 201, result.text
    paths = result.json()["paths"]
    assert paths
    assert all(path["confidence_label"] == "Low" for path in paths)
    assert all(0 <= path["confidence_score"] <= 1 for path in paths)


def test_catalog_routes_remain_public():
    assert client.get("/api/v1/roles").status_code == 200
    assert client.get("/api/v1/skills").status_code == 200
    assert client.get("/api/v1/skill-categories").status_code == 200
