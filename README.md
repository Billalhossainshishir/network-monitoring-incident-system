# Network Monitoring & Incident System

A recruiter-facing portfolio project that demonstrates **IT support, infrastructure monitoring, backend APIs, operational metrics and incident automation**.

The system monitors five simulated services, records availability and latency, waits for repeated failures before creating an incident, and resolves the incident automatically when the service recovers.

> **Deployment status:** intentionally **not live yet**. The project is being tested locally before public deployment.

## Recruiter demo flow

**Services online → health checks run → simulate outage → repeated failures → incident created → restore service → incident resolved**

## What this project proves

- Service health checking and latency tracking
- Repeated-failure logic to reduce alert noise
- Automatic incident creation and recovery
- Uptime and latency metrics
- Incident history and monitoring logs
- FastAPI backend design
- Relational data modelling with SQLAlchemy
- PostgreSQL-ready configuration
- Automated tests
- Recruiter-friendly dashboard

## Monitored services

- Web Server
- API Server
- Database Service
- Authentication Service
- File Service

All targets are simulated, so the demo never interferes with third-party infrastructure.

## Incident logic

```text
Check 1 failed → Check 2 failed → Check 3 failed → Incident created
Service recovers → Recovery check succeeds → Incident automatically resolved
```

The failure threshold is configurable using `FAILURE_THRESHOLD` and defaults to `3`.

## Local setup

```bash
git clone https://github.com/Billalhossainshishir/network-monitoring-incident-system.git
cd network-monitoring-incident-system
python -m venv .venv
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`.

## How to test the main incident workflow

1. Open the dashboard.
2. Choose **API Server**.
3. Click **Simulate Failure**.
4. Click **Run Check** three times.
5. Confirm the API Server becomes OFFLINE and an ACTIVE incident appears.
6. Click **Restore Service**.
7. Confirm the incident changes to RESOLVED and a duration is recorded.
8. Click **Reset Incidents** to return to the clean demo state.

The background monitor also runs automatically every two seconds unless disabled in configuration.

## Core API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Application health |
| GET | `/api/services` | List monitored services |
| GET | `/services/{slug}/health` | Simulated target health endpoint |
| POST | `/api/services/{slug}/simulate-failure` | Force a simulated outage |
| POST | `/api/services/{slug}/restore` | Restore service and trigger recovery |
| POST | `/api/monitor/run-check` | Run a full monitoring cycle |
| GET | `/api/checks` | Monitoring history |
| GET | `/api/incidents` | Incident history |
| GET | `/api/incidents/{id}/events` | Incident lifecycle events |
| GET | `/api/metrics` | Uptime, latency and outage metrics |
| GET | `/api/dashboard` | Combined dashboard payload |
| POST | `/api/reset` | Reset demo data |

## Database

SQLite is used by default for quick local testing. The data layer is PostgreSQL-ready for later deployment.

Core tables:

- `monitored_services`
- `monitoring_checks`
- `incidents`
- `incident_events`

## Automated tests

```bash
pytest -q
```

Tests cover the seeded services, three-failure incident rule, automatic recovery and operational metrics.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Planned later enhancement

After the standalone monitor is validated, it can call the **AI Helpdesk Copilot** API when an incident is created:

```text
Network monitor detects outage
→ incident created
→ Helpdesk API called
→ support ticket created automatically
```

That integration is intentionally not required for the first Project 3 test build.

## CV / portfolio description

Built a Python-based network/service monitoring platform that records uptime and latency, applies repeated-failure logic, creates and resolves incidents automatically, and visualises operational health through a live dashboard.
