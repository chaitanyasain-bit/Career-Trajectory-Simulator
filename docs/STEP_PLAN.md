# Step Plan — Career Trajectory Simulator

> Build for Bharat 2.0 · Team Valyrians

This document tracks the implementation steps. Each step must be completed and reviewed before the next begins.

---

## Step 1 — Foundation ✅ (current)
- [x] Inspect workspace (was empty)
- [x] Create directory scaffold: `frontend/`, `backend/`, `data/`, `tests/`, `docs/`
- [x] `README.md` with product purpose and planned stack
- [x] `docs/ARCHITECTURE.md` — full system design
- [x] Backend: FastAPI app factory, config, DB session, exceptions
- [x] Backend: `requirements.txt`, `requirements-dev.txt`, `.env.example`
- [x] Data engine: typed stubs for `TrajectoryEngine`, `CareerGraph`, `confidence`, `gap_analysis`
- [x] Frontend: `package.json`, `vite.config.ts`, `tsconfig.json`, Tailwind, PostCSS
- [x] Frontend: `index.html`, `main.tsx`, `App.tsx` (placeholder), `index.css`
- [x] Frontend: shared TypeScript types (`src/types/index.ts`)
- [x] Frontend: API client stub (`src/services/api.ts`)
- [x] `pyproject.toml` with pytest, ruff, mypy config
- [x] Tests: smoke tests for health endpoint and data engine stubs
- [x] `frontend/.npmrc` (legacy-peer-deps)
- [x] `frontend/node_modules/` installed

---

## Step 2 — Database + Backend API (Completed)
- [x] Define SQLAlchemy ORM models (User, Profile, Simulation, SimulationPath, SkillGap)
- [x] Create Alembic migration for initial schema
- [x] Pydantic request/response schemas
- [x] Seed database script and test offline capabilities with aiosqlite
- [x] FastAPI route implementations for `/profiles`, `/simulate`, `/history`
- [x] `pytest` suite for all routes with TestClient

---

## Step 3 — Trajectory Engine (Completed)
- [x] Build career knowledge graph with NetworkX (seed data)
- [x] Implement feature vector construction from UserProfile
- [x] Implement confidence scoring (cosine similarity v1)
- [x] Implement BFS path discovery
- [x] Implement `gap_analysis.compute_gaps()`
- [x] Implement What-If delta engine
- [x] Unit tests for all engine modules

---

## Step 4 — Roadmap Generator (planned)
- [ ] Rule-based roadmap step generation
- [ ] Skill prioritization by impact score
- [ ] `/api/v1/roadmap/{path_id}` endpoint

---

## Step 5 — Frontend UI (planned)
- [ ] React Router setup with page shells
- [ ] ProfileForm component
- [ ] SimulationResult component (paths + confidence bars)
- [ ] PathCompare component
- [ ] WhatIf panel
- [ ] Roadmap timeline view
- [ ] SimulationHistory page
- [ ] Zustand store wiring
- [ ] TanStack Query integration

---

## Step 6 — Integration + Polish (planned)
- [ ] End-to-end flow: form → API → engine → DB → UI
- [ ] Error handling throughout
- [ ] Docker Compose (optional)
- [ ] Performance tuning

---

## Future (post-hackathon)
- XGBoost confidence model
- Sentence Transformers for skill matching
- Neo4j graph migration
- LLM-generated roadmap text
- Live market signals
