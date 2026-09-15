# Architecture

```mermaid
flowchart LR
    A[Simulated Services] --> B[Monitoring Worker]
    B --> C[Health Check + Latency]
    C --> D[(Monitoring Checks)]
    C --> E{Consecutive failures >= 3?}
    E -- Yes --> F[Create Active Incident]
    E -- No --> G[Continue Monitoring]
    F --> H[(Incidents + Incident Events)]
    A -->|Service restored| I[Recovery Check]
    I --> J[Resolve Active Incident]
    J --> H
    D --> K[FastAPI]
    H --> K
    K --> L[Recruiter Dashboard]
```

## Data model

- `monitored_services`: service identity, simulated state and current failure streak.
- `monitoring_checks`: timestamped availability, HTTP code and latency result.
- `incidents`: automatically created after repeated failures and automatically resolved after recovery.
- `incident_events`: lifecycle timeline for incident creation, continued failure and recovery.

## Monitoring rule

A single failed check does not create an incident. The default threshold is three consecutive failures. This reduces alert noise and demonstrates false-positive-aware monitoring behaviour.
