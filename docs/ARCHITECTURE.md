# Architecture — Career Trajectory Simulator

> **Hackathon:** Build for Bharat 2.0 | **Team:** Valyrians

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                                │
│                  React + TypeScript + Tailwind CSS                  │
└─────────────────────────┬───────────────────────────────────────────┘
                          │  HTTPS / REST + JSON
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API LAYER  (FastAPI)                             │
│   /api/v1/profiles  /simulate  /roadmap  /history  /whatif         │
└────────────┬──────────────────────────┬────────────────────────────┘
             │                          │
             ▼                          ▼
┌────────────────────┐      ┌───────────────────────────────────────┐
│  PostgreSQL 15+    │      │       Data / ML Engine (Python)       │
│  (Persistent       │      │   Pandas · NumPy · scikit-learn       │
│   storage)         │      │   NetworkX · (future: XGBoost)        │
└────────────────────┘      └───────────────────────────────────────┘
```

---

## 2. Frontend

### Stack
| Concern | Technology |
|---------|-----------|
| Framework | React 18 |
| Language | TypeScript 5 |
| Build tool | Vite 5 |
| Styling | Tailwind CSS 3 |
| State management | Zustand (planned) |
| Data fetching | TanStack Query (React Query) |
| Charts | Recharts |
| Routing | React Router v6 |

### Directory Layout
```
frontend/
├── public/                    # Static assets
└── src/
    ├── assets/                # Images, icons, fonts
    ├── components/            # Reusable UI components
    │   ├── ui/                #   Primitive components (Button, Card …)
    │   ├── simulation/        #   Simulation-specific widgets
    │   └── layout/            #   Header, Sidebar, Shell
    ├── pages/                 # Route-level pages
    │   ├── Home.tsx
    │   ├── Simulate.tsx
    │   ├── Compare.tsx
    │   ├── Roadmap.tsx
    │   └── History.tsx
    ├── hooks/                 # Custom React hooks
    ├── services/              # API client (axios / fetch wrappers)
    ├── store/                 # Zustand stores
    ├── types/                 # Shared TypeScript interfaces
    └── utils/                 # Pure utility functions
```

### Key Design Decisions
- **No Redux** — Zustand is leaner and sufficient for this scope.
- **TanStack Query** handles server-state caching and background refetching.
- All API calls go through `src/services/api.ts` — a single, typed client.
- Types defined in `src/types/` are the single source of truth shared with backend schemas.

---

## 3. Backend

### Stack
| Concern | Technology |
|---------|-----------|
| Framework | FastAPI |
| Language | Python 3.11+ |
| Server | Uvicorn (ASGI) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | Scrypt password hashes + signed JWT bearer tokens |

### Directory Layout
```
backend/
├── app/
│   ├── main.py               # FastAPI app factory, router registration
│   ├── config.py             # Settings via pydantic-settings
│   ├── api/
│   │   └── v1/
│   │       └── routes/       # One file per resource
│   │           ├── profiles.py
│   │           ├── simulation.py
│   │           ├── roadmap.py
│   │           ├── history.py
│   │           └── whatif.py
│   ├── core/
│   │   ├── security.py       # JWT helpers
│   │   └── exceptions.py     # Custom HTTP exceptions
│   ├── db/
│   │   ├── session.py        # Async engine + session factory
│   │   └── base.py           # Declarative base
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── profile.py
│   │   └── simulation.py
│   ├── schemas/              # Pydantic request/response schemas
│   │   ├── profile.py
│   │   └── simulation.py
│   ├── services/             # Business logic layer
│   │   ├── trajectory.py     # Calls into data/engine
│   │   ├── roadmap.py
│   │   └── history.py
│   └── utils/                # Shared helpers
├── migrations/               # Alembic migration scripts
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Register account and issue access token |
| `POST` | `/api/v1/auth/login` | Verify credentials and issue access token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated account |
| `POST` | `/api/v1/profiles/me` | Create authenticated user's profile |
| `GET` | `/api/v1/profiles/me` | Fetch authenticated user's profile |
| `PATCH` | `/api/v1/profiles/me` | Partially update authenticated user's profile |
| `GET` | `/api/v1/roles` | Search and page through career roles |
| `GET` | `/api/v1/roles/{role_id}` | Fetch role catalog detail |
| `GET` | `/api/v1/skills` | Search and page through skills; filter by category |
| `GET` | `/api/v1/skills/{skill_id}` | Fetch skill with category |
| `GET` | `/api/v1/skill-categories` | List skill categories with skill counts |
| `GET` | `/api/v1/skill-categories/{category_id}` | Fetch skill category with count |
| `POST` | `/api/v1/simulate/{profile_id}` | Run career trajectory simulation |
| `POST` | `/api/v1/simulate/{simulation_id}/whatif` | Persist a linked What-If scenario and comparison |
| `GET` | `/api/v1/roadmap/{path_id}` | Fetch persisted roadmap steps |
| `GET` | `/api/v1/history/{profile_id}` | List simulations and linked scenarios |
| `GET` | `/api/v1/history/detail/{simulation_id}` | Fetch a saved simulation result |
| `GET` | `/api/v1/history/replay/{simulation_id}` | Replay saved results without recalculation |

Authenticated requests use `Authorization: Bearer <token>`. User-owned profile,
simulation, history, and roadmap resources are scoped to the authenticated
account. Role/skill catalogs are public and read-only.
Profile patch fields are optional; omitted scalar and collection fields remain
unchanged. Supplying a collection replaces that collection for the profile.

---

## 4. Database Architecture (PostgreSQL)

### Design Principles
- UUID primary keys everywhere, automatically generated at insertion.
- `created_at` / `updated_at` timestamps on every table managed by mixins.
- Strict constraint enforcement (check constraints, foreign keys).
- Alembic manages all schema changes. Raw SQL DDL is avoided.
- A fully normalized schema where career data (roles, skills, transitions) is decoupled from user data.

### Planned Entity Relationships (ERD)

```text
Global Catalogs:
  skill_categories (1) ─── (N) skills
  roles (1) ─── (N) role_skill_requirements (N) ─── (1) skills
  roles (1) ─── (N) role_transitions (N) ─── (1) roles

User Data:
  users (1) ─── (1) user_profiles
  user_profiles (1) ─── (N) user_skills (N) ─── (1) skills
  user_profiles (1) ─── (N) educations
  user_profiles (1) ─── (N) work_experiences

Simulations:
  user_profiles (1) ─── (N) simulations
  simulations (1) ─── (N) simulation_paths
  simulation_paths (1) ─── (1) roles (target)
  simulation_paths (1) ─── (N) skill_gaps (N) ─── (1) skills
  simulation_paths (1) ─── (N) roadmap_steps
```

### Setup & Migration Instructions

1. **Prerequisites:** Install Python 3.11+ and PostgreSQL 15+, then activate the backend virtual environment.
2. **Environment File:** Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL` to the PostgreSQL asyncpg connection URL for your database. Settings load this file from the backend directory regardless of the command's working directory. SQLite is supported for isolated tests, not the documented application database.
3. **Database Initialization:** From the `backend/` directory, run Alembic to apply schema migrations. Catalog requests require seeded reference data:
   ```bash
   cd backend
   python -m alembic upgrade head
   ```
4. **Seed Database:** From the `backend/` directory, populate the database with the core skill sets, roles, and transitions:
   ```bash
   python -m app.db.run_seed
   ```

5. **Run the API:** From the repository root, expose both the `backend/` and root packages on `PYTHONPATH` before starting Uvicorn. For example, in Windows PowerShell:
   ```powershell
   $env:PYTHONPATH = "backend;."
   python -m uvicorn app.main:app --reload
   ```
   On macOS/Linux, use `PYTHONPATH=backend:. python -m uvicorn app.main:app --reload`.

6. **Run backend tests:** From the repository root, set `DATABASE_URL=sqlite+aiosqlite:///:memory:` and run `python -m pytest`. Tests use isolated in-memory SQLite and do not require PostgreSQL.

---

## 5. Data Layer & ML / Trajectory Engine

### Location: `data/`
```
data/
├── engine/
│   ├── trajectory.py         # Core path simulation logic
│   ├── graph.py              # Career graph (NetworkX)
│   ├── confidence.py         # Confidence scoring
│   ├── gap_analysis.py       # Skill gap calculator
│   └── whatif.py             # What-If delta computation
├── pipeline/
│   ├── preprocess.py         # Data cleaning and normalisation
│   ├── feature_engineering.py
│   └── loaders.py            # Dataset loaders
├── models/                   # Trained model artefacts (.pkl, .joblib)
└── datasets/                 # Raw / processed data files (.gitignored)
```

### Trajectory Simulation — Conceptual Flow

```
User Profile Input
       │
       ▼
  [Feature Vector]  ← skills encoded, experience quantified
       │
       ▼
  [Career Graph]   ← NetworkX directed graph of roles and transitions
       │
       ▼
  [Path Discovery] ← BFS / shortest-path from current node
       │
       ▼
  [Confidence Scoring] ← cosine similarity + rule-based scoring
                          (future: XGBoost classifier)
       │
       ▼
  [Gap Analysis]   ← set difference between user skills and path skills
       │
       ▼
  [Roadmap Gen]    ← ordered steps sorted by impact + dependency
       │
       ▼
  Simulation Result (JSON → stored in DB → returned to frontend)
```

### What-If Simulation
- Clone the profile and catalog snapshot attached to the selected simulation.
- Apply hypothetical skill additions/proficiency changes, experience, and projects
  without writing to the user's profile.
- Persist the scenario as a child simulation and compare its paths, confidence,
  skill gaps, and roadmap steps with the saved parent result.
- Original simulation inputs and outputs are kept for deterministic history
  replay; replay reads the persisted result and does not rerun the current engine.

### Simulation Engine
- Career roles, skill requirements, proficiency expectations, and transitions are
  loaded from PostgreSQL for each new baseline simulation; NetworkX ranks reachable
  roles and uses transition weights in explainable confidence scores.
- Each role-skill requirement stores an explicit target proficiency (1–5). Bundled
  catalog entries without a separately curated target are seeded using a documented
  importance-based default; migrations backfill existing requirements with the same
  mapping.
- Confidence combines proficiency-adjusted role-skill coverage (60%), transition
  likelihood (20%), experience fit (10%), and profile evidence (10%).
- Every simulation stores a profile, catalog, engine-version, and result snapshot.
  Skill gaps and generated, ordered roadmap steps are also persisted as relational
  rows for querying and authorization.

### Planned ML Models
| Model | Purpose | Library |
|-------|---------|---------|
| Skill Encoder | Encode skill strings to embeddings | scikit-learn TF-IDF → future: Sentence Transformers |
| Confidence Scorer | Score feasibility of a transition | scikit-learn (Logistic Regression → future: XGBoost) |
| Gap Ranker | Rank skills by learning priority | Custom scoring function |
| Career Graph | Model role-to-role transitions | NetworkX DiGraph |

---

## 6. Cross-Cutting Concerns

### Configuration
- All secrets via environment variables (`.env`).
- `pydantic-settings` on backend; Vite `VITE_*` env vars on frontend.
- `.env.example` files committed; `.env` gitignored.

### Error Handling
- Backend: Custom `AppException` → mapped to HTTP responses with structured JSON.
- Frontend: Error boundaries + TanStack Query `onError` handlers.

### Logging
- Backend: Python `structlog` — structured JSON logs.
- Frontend: (future) Sentry.

### Testing Strategy
| Layer | Tool | Coverage target |
|-------|------|----------------|
| Backend unit | Pytest + httpx (TestClient) | ≥80% |
| Data / ML | Pytest | ≥70% |
| Frontend unit | Vitest + React Testing Library | ≥70% |
| E2E | Playwright (future) | Critical paths |

---

## 7. Communication Flow (Request Lifecycle)

```
1. User fills profile form in React UI
2. Frontend → POST /api/v1/simulate  (JSON body)
3. FastAPI router validates with Pydantic schema
4. Service layer calls data/engine/trajectory.py
5. Engine builds feature vector → queries career graph → scores paths
6. Results returned to service → written to PostgreSQL
7. Response JSON sent back to frontend
8. TanStack Query caches response
9. React renders SimulationResult component with paths + confidence + gaps
```

---

## 8. Future Architecture Extensions

| Extension | Trigger condition |
|-----------|------------------|
| **Neo4j** | Career graph exceeds 10k nodes; complex graph queries needed |
| **XGBoost** | Confidence model accuracy < 80% with logistic regression |
| **Sentence Transformers** | Skill text matching quality insufficient |
| **LLM / NLP** | Free-text roadmap generation required |
| **Market Signals** | Live job-posting data integration justified |
| **Redis Cache** | Simulation latency > 2s under load |
| **Celery** | Simulations need async background processing |

---

*Last updated: Step 1 — Foundation*
