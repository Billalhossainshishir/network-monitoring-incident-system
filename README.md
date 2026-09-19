# Network Monitoring & Incident System

An incident-management project for five simulated services. Repeated failures create one active incident; a successful check resolves it and records the recovery. The backend demonstrates the incident lifecycle using simulated observations rather than probing external servers.

Read the [reviewer guide](docs/REVIEWER_GUIDE.md) for execution modes, reproducible setup, architecture, verification steps and known limitations.

The project monitors five simulated services, records availability and latency, waits for repeated failures before creating an incident, resolves the incident automatically when the service recovers, and visualises the operational state through a dashboard.

## Portfolio strategy

This repository intentionally contains **two experiences**.

### 1. Full engineering project

The repository contains the actual backend implementation:

- Python + FastAPI
- SQLAlchemy data model
- SQLite for low-friction local testing
- PostgreSQL-ready Docker Compose stack
- configurable background monitoring worker
- three-consecutive-failure incident logic
- automatic recovery and incident resolution
- incident event timeline
- operational metrics
- backend-connected HTML/CSS/JavaScript dashboard
- optional AI Helpdesk Copilot integration
- automated pytest suite
- GitHub Actions CI
- architecture, API, testing and case-study documentation

### 2. Instant recruiter demo

**GitHub Pages target URL:**  
https://billalhossainshishir.github.io/network-monitoring-incident-system/

The root `index.html` and `assets/` directory contain a browser-only simulation of the same incident lifecycle.

The demo is intentionally static so it can open instantly on GitHub Pages without a hosted Python server, PostgreSQL database or recruiter login. The guided public demo uses manual health checks so the three-failure incident threshold is deterministic and easy to follow.

> **Transparency:** the GitHub Pages demo simulates the monitoring workflow in JavaScript. It is not presented as a deployed FastAPI/PostgreSQL backend. The full server-side implementation is included in this repository and can be run locally.

## Recruiter demo flow

```text
Services online
→ Simulate Failure
→ Check 1 fails
→ Check 2 fails
→ Check 3 fails
→ ACTIVE incident created
→ Restore Service
→ recovery check succeeds
→ incident RESOLVED
→ duration recorded
```

The main interaction can be understood in approximately 30–60 seconds.

## Monitored services

- Web Server
- API Server
- Database Service
- Authentication Service
- File Service

All services are simulated for safe portfolio testing.

## Why three consecutive failures?

Creating an incident on the first failed check can create alert noise.

This project uses a configurable threshold:

```text
Failure 1 → monitoring event only
Failure 2 → monitoring event only
Failure 3 → confirmed outage → incident created
```

Default:

```text
FAILURE_THRESHOLD=3
```

## Automatic recovery

When an offline service returns online:

```text
successful recovery check
→ active incident found
→ incident status = RESOLVED
→ resolved_at stored
→ outage duration calculated
→ RECOVERY event added
```

## Architecture

### Full implementation

```text
Simulated services
        ↓
Background monitoring worker
        ↓
Health / latency observations
        ↓
monitoring_checks
        ↓
Consecutive-failure engine
        ├── below threshold → keep monitoring
        └── threshold reached → ACTIVE incident
                                  ↓
                            incident_events
                                  ↓
                       optional Helpdesk API

Service recovers
        ↓
successful check
        ↓
incident RESOLVED
        ↓
duration + recovery event
        ↓
FastAPI dashboard / metrics API
        ↓
backend-connected frontend
```

### GitHub Pages demo

```text
Browser service simulator
        ↓
JavaScript health checks
        ↓
in-memory logs
        ↓
same 3-failure business rule
        ↓
incident + recovery simulation
        ↓
Chart.js dashboard
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Repository structure

```text
.
├── index.html                     # GitHub Pages recruiter demo
├── assets/
│   ├── css/style.css
│   └── js/app.js
│
├── backend/
│   ├── Dockerfile
│   ├── run.py
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── db.py
│       ├── models.py
│       ├── schemas.py
│       ├── api/
│       │   └── routes.py
│       └── services/
│           ├── monitor.py
│           └── helpdesk.py
│
├── frontend/                      # Real FastAPI-connected frontend
│   ├── index.html
│   ├── css/app.css
│   └── js/app.js
│
├── tests/
│   └── test_api.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── TESTING.md
│   └── CASE_STUDY.md
│
├── .github/workflows/tests.yml
├── .env.example
├── .dockerignore
├── .gitignore
├── .nojekyll
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

## Database model

### `monitored_services`

Stores:

- service slug
- display name
- description
- simulated online/offline state
- current consecutive-failure count

### `monitoring_checks`

Stores:

- service
- timestamp
- ONLINE / OFFLINE status
- response latency
- HTTP result

### `incidents`

Stores:

- incident number
- service
- ACTIVE / RESOLVED state
- opened timestamp
- resolved timestamp
- duration
- trigger reason

### `incident_events`

Stores an auditable lifecycle timeline:

- incident created
- additional failed check
- recovery
- optional Helpdesk integration result

## Operational metrics

The backend calculates per-service:

- uptime percentage
- average latency
- maximum latency
- outage count
- longest outage
- last successful check
- incident count

The dashboard also presents:

- online services
- offline services
- active incidents
- recent average latency
- recent monitoring logs
- incident history

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | application health |
| `GET` | `/api/services` | monitored services |
| `GET` | `/services/{slug}/health` | simulated target health |
| `POST` | `/api/services/{slug}/simulate-failure` | trigger outage |
| `POST` | `/api/services/{slug}/restore` | restore and recover |
| `POST` | `/api/monitor/run-check` | execute monitoring cycle |
| `GET` | `/api/checks` | monitoring history |
| `GET` | `/api/incidents` | incident history |
| `GET` | `/api/incidents/{id}/events` | incident timeline |
| `GET` | `/api/metrics` | operational metrics |
| `GET` | `/api/dashboard` | combined dashboard data |
| `POST` | `/api/reset` | reset demo data |

Detailed API documentation: [docs/API.md](docs/API.md)

## Run locally — Python

Python 3.14 is supported by the pinned project dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

Open:

```text
API root:     http://127.0.0.1:8000
Swagger docs: http://127.0.0.1:8000/docs
```

In a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```

## Local test flow

1. Start the backend.
2. Start the frontend.
3. Select **API Server**.
4. Click **Simulate Failure**.
5. Run three health checks.
6. Confirm an ACTIVE incident appears.
7. Click **Restore Service**.
8. Confirm the incident becomes RESOLVED.
9. Inspect latency, monitoring logs and incident history.

## Run with Docker + PostgreSQL

Requirements:

- Docker Desktop / Docker Engine
- Docker Compose

Run:

```bash
docker compose up --build
```

The Docker stack runs the API and PostgreSQL. It does not serve the dashboard: run `python -m http.server 5500 --directory frontend` separately from the repository root and open http://127.0.0.1:5500.

Stop:

```bash
docker compose down
```

Remove the database volume:

```bash
docker compose down -v
```

## Automated testing

Run:

```bash
pytest -q
```

The suite covers:

- application health
- five seeded services
- simulated service-health status
- no incident before the threshold
- incident creation on the third failure
- no duplicate ACTIVE incident during continued outage
- incident event timeline
- automatic recovery
- dashboard response shape
- operational metrics
- reset behaviour

GitHub Actions runs the tests automatically on pushes and pull requests.

See [docs/TESTING.md](docs/TESTING.md).

## Optional Project 1 integration

The project can connect to the **AI Helpdesk Copilot**.

Flow:

```text
Network monitor confirms outage
→ incident created
→ Helpdesk /tickets API called
→ support ticket created automatically
```

The Python process does not load `.env` automatically. Set these process environment variables before startup (see the reviewer guide for PowerShell commands):

```text
HELPDESK_INTEGRATION_ENABLED=true
HELPDESK_API_URL=http://127.0.0.1:8001
```

The integration is failure-safe. If the Helpdesk API is unavailable, the monitoring platform continues running and records a `HELPDESK_SYNC_FAILED` incident event.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Testing Strategy](docs/TESTING.md)
- [Case Study](docs/CASE_STUDY.md)

## Case study

Read [docs/CASE_STUDY.md](docs/CASE_STUDY.md) for the problem, engineering decisions and recruiter-facing explanation.

## CV / portfolio wording

**Network Monitoring & Incident System — Sep 2026**  
Built a Python/FastAPI service-monitoring platform that records uptime and latency, applies configurable repeated-failure logic to reduce alert noise, creates and resolves incidents automatically, stores lifecycle events and operational metrics, supports PostgreSQL/Docker deployment, integrates optionally with an AI Helpdesk API, and includes an interactive GitHub Pages recruiter demo.

## Design decision: why the live demo is separate

A public portfolio link should open quickly and remain reliable.

GitHub Pages provides that experience but cannot execute Python/FastAPI or host PostgreSQL.

Instead of pretending that a static page is a deployed backend:

- **GitHub Pages** demonstrates the product behaviour interactively.
- **The repository** proves the actual engineering implementation.

That separation is intentional, transparent and documented.
