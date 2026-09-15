# Testing Strategy

The backend test suite focuses on the incident lifecycle and API behaviour that matter most to the project.

## Run locally

```powershell
python -m pytest -q
```

## Automated CI

GitHub Actions runs the test suite on:

- pushes to `main`
- pull requests targeting `main`

The workflow uses Python 3.14 to match the current supported local setup.

## Core scenarios

### Application starts and services are seeded

Expected:

- health endpoint returns 200
- five services exist
- stable service slugs are present

### No premature incident

Expected:

- first failed check: no incident
- second consecutive failed check: no incident

This verifies alert-noise reduction.

### Third failure creates incident

Expected:

- third consecutive failure creates exactly one ACTIVE incident
- trigger reason references the configured threshold

### Continued failure does not duplicate incident

Expected:

- additional failed checks append lifecycle events
- only one ACTIVE incident exists for the service

### Recovery resolves incident

Expected:

- restoring the service records a successful check
- incident becomes RESOLVED
- resolved timestamp is stored
- duration is calculated

### Metrics endpoint

Expected operational fields:

- uptime percentage
- average latency
- maximum latency
- outage count
- longest outage
- last successful check

### Reset

Expected:

- incidents removed
- monitoring logs removed
- every service returned to online demo state

## Why these tests matter

The important behaviour is not simply whether API endpoints return JSON. The tests verify the business rules that define the monitoring system:

```text
persistent failure → one incident
recovery → deterministic resolution
```
