# Career Trajectory Simulator

> **Hackathon:** Build for Bharat 2.0
> **Team:** Valyrians

---

## What is this?

**Career Trajectory Simulator** answers the question:

> *"What career paths can I realistically build from my current state?"*

This is **not** a job recommendation engine. It is a **forward-looking simulator** that:

1. Accepts a user's current role, skills, experience, and projects
2. Simulates multiple possible career paths with confidence scores
3. Compares paths side-by-side
4. Runs **What-If simulations** — "What happens if I learn X or complete project Y?"
5. Calculates skill gaps for each path
6. Generates a practical, time-bound roadmap
7. Stores and replays simulation history

---

## Example

**Current state:**
- Role: Data Analyst
- Skills: Python, SQL, Excel, Pandas

**Simulated paths:**
| Path | Confidence | Gap Count |
|------|-----------|-----------|
| Data Scientist | High | 3 skills |
| ML Engineer | Medium | 6 skills |
| Data Engineer | Medium | 4 skills |
| Product Manager | Low | 8 skills |

---

## Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS |
| **Backend** | Python 3.11+ + FastAPI + Uvicorn |
| **Database** | PostgreSQL 15+ (SQLite supported for isolated tests) |
| **ORM** | SQLAlchemy 2.0 + Alembic (migrations) |
| **Data / ML** | Pandas + NumPy + scikit-learn + NetworkX |
| **Testing** | Pytest (backend) · Vitest (frontend) |
| **Auth** | Account registration/login with signed JWT bearer tokens |
| **Containerization** | Docker + Docker Compose (planned) |

**Future extensions (if justified by complexity):**
- XGBoost for path-confidence scoring
- Sentence Transformers for skill semantic matching
- Neo4j for career graph storage
- NLP/LLM for roadmap generation
- Live market signals (job-posting APIs)

---

## Project Structure

```
Career-Trajectory-Simulator/
├── frontend/          # React + TypeScript + Vite + Tailwind
├── backend/           # FastAPI application
├── data/              # ML engine, pipelines, datasets
├── tests/             # All test suites
└── docs/              # Architecture and design docs
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system design.

---

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- (Optional) Docker + Docker Compose

### Backend

```bash
# From the repository root; create and activate a virtual environment.
cd backend
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

On macOS/Linux, activate with `source .venv/bin/activate` and run the same
`pip install` command. Copy `.env.example` to `.env` using the platform's
normal file-copy command.

Set `DATABASE_URL` in `backend/.env` to a PostgreSQL async connection URL for
your local database:

```text
DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5432/career_simulator
```

Apply the schema and load the initial role/skill catalog from `backend/`:

```bash
python -m alembic upgrade head
python -m app.db.run_seed
```

Start the API from the repository root so both the backend application and the
top-level `data` package are importable. On Windows PowerShell:

```powershell
Set-Location ..
$env:PYTHONPATH = "backend;."
python -m uvicorn app.main:app --reload
```

On macOS/Linux:

```bash
cd ..
PYTHONPATH=backend:. python -m uvicorn app.main:app --reload
```

The API documentation is available at `http://localhost:8000/api/docs`; the
database-aware health check is at `http://localhost:8000/health`.
Register with `POST /api/v1/auth/register`, sign in with
`POST /api/v1/auth/login`, and send the returned bearer token to authenticated
profile and simulation routes. Use `/api/v1/auth/me` to retrieve the current
account.
Read-only reference catalogs are available at `/api/v1/roles`,
`/api/v1/skills`, and `/api/v1/skill-categories`. These support `search`,
`limit`, and `offset`; roles can also be filtered by `domain`, and skills by
`category_id`.

Run a simulation for the authenticated user's saved profile with
`POST /api/v1/simulate/{profile_id}`. Submit a scenario against a saved run at
`POST /api/v1/simulate/{simulation_id}/whatif`; it accepts skill IDs,
proficiency overrides, additional experience months, and hypothetical projects.
Scenarios are saved as linked simulations and never update the real profile.
Saved results and roadmaps are available from `/api/v1/history/{profile_id}`,
`/api/v1/history/replay/{simulation_id}`, and `/api/v1/roadmap/{path_id}`.

### Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` requests to the FastAPI service at
`http://localhost:8000`. The frontend provides registration/login and protected
workspace routes for the dashboard, profile, career simulation, career details,
path comparison, What-If scenarios, roadmaps, and saved simulation history.
The dashboard and saved simulation results also include an interactive 3D career
map built from the simulation's persisted career paths and transition routes.
When WebGL is unavailable, the same recommendations remain accessible through
the career-path list and details panel.

Validate the frontend with:

```bash
npm test -- --run
npm run lint
npm run build
```

### Tests

Backend tests can use an in-memory SQLite database without requiring a running
PostgreSQL service. From the repository root, in Windows PowerShell:

```powershell
$env:DATABASE_URL = "sqlite+aiosqlite:///:memory:"
python -m pytest
```

On macOS/Linux:

```bash
DATABASE_URL=sqlite+aiosqlite:///:memory: python -m pytest
```

---

## License

MIT © Team Valyrians – Build for Bharat 2.0
