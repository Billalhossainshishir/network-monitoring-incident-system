# Architecture

The project intentionally has two execution paths: a full engineering implementation and an instant static recruiter demo.

## Full engineering implementation

```mermaid
flowchart LR
    A[Simulated Services] --> B[Background Monitoring Worker]
    B --> C[Health Check + Latency Observation]
    C --> D[(monitoring_checks)]
    C --> E{Consecutive failures >= threshold?}
    E -- No --> F[Continue Monitoring]
    E -- Yes --> G[Create ACTIVE Incident]
    G --> H[(incidents)]
    G --> I[(incident_events)]
    G --> J{Helpdesk integration enabled?}
    J -- Yes --> K[AI Helpdesk Copilot API]
    J -- No --> L[Standalone Monitoring]
    A -->|Restored| M[Successful Recovery Check]
    M --> N[Resolve Incident + Calculate Duration]
    N --> H
    N --> I
    D --> O[FastAPI Dashboard API]
    H --> O
    I --> O
    O --> P[Backend-Connected Frontend]
```

## GitHub Pages demo

```mermaid
flowchart LR
    A[Browser Service Simulator] --> B[JavaScript Health Checks]
    B --> C[In-Memory Monitoring Logs]
    B --> D{3 consecutive failures?}
    D -- Yes --> E[Browser Incident Created]
    A -->|Restore| F[Recovery]
    F --> G[Browser Incident Resolved]
    C --> H[Chart.js Dashboard]
    E --> H
    G --> H
```

The GitHub Pages path intentionally contains no FastAPI, SQLAlchemy or PostgreSQL execution. Those technologies are represented by the full repository implementation.

## Backend components

### FastAPI application

Provides:

- service-control endpoints
- monitoring-cycle endpoint
- monitoring history
- incident history
- incident event timeline
- operational metrics
- dashboard aggregation

### Monitoring worker

Runs on a configurable interval and performs checks across configured services.

Default:

```text
MONITOR_INTERVAL_SECONDS=2
```

### Incident engine

An incident is created only after the configured consecutive-failure threshold.

Default:

```text
FAILURE_THRESHOLD=3
```

### Recovery engine

A successful check on a service with an ACTIVE incident:

1. marks the incident RESOLVED
2. records `resolved_at`
3. calculates outage duration
4. creates a RECOVERY incident event

### Persistence

SQLAlchemy models:

- `monitored_services`
- `monitoring_checks`
- `incidents`
- `incident_events`

Local development defaults to SQLite.

Docker Compose uses PostgreSQL.

## Frontends

### `frontend/`

Real backend-connected dashboard.

It expects FastAPI at:

```text
http://127.0.0.1:8000
```

### root `index.html` + `assets/`

Standalone recruiter demo for GitHub Pages.

This version simulates the monitoring logic in browser memory.

## Cross-project integration

When enabled:

```text
Network Monitoring & Incident System
        ↓
incident created
        ↓
AI Helpdesk Copilot /tickets
        ↓
support workflow
```

Integration is optional and failure-safe.

## Safety

The project uses simulated services rather than probing arbitrary third-party systems. This keeps the portfolio demo repeatable and avoids creating traffic against systems the project does not own.
