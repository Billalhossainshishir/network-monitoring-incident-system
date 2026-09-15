# API Reference

The FastAPI backend exposes operational endpoints for simulated service health, monitoring, incident lifecycle data and metrics.

## Base URL

Local development:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## Application endpoints

### `GET /`

Returns project metadata and current backend status.

### `GET /health`

Application-level health probe.

Example:

```json
{
  "status": "healthy"
}
```

## Service endpoints

### `GET /api/services`

Returns all monitored services and their current simulated state.

### `GET /services/{slug}/health`

Returns a health response for one simulated service.

Possible responses:

- HTTP 200: service online
- HTTP 503: service offline

Supported slugs:

- `web`
- `api`
- `database`
- `auth`
- `file`

### `POST /api/services/{slug}/simulate-failure`

Forces the selected service into demo outage mode and resets its consecutive-failure counter.

### `POST /api/services/{slug}/restore`

Restores the selected service and immediately records a successful recovery check. Any active incident for that service is resolved automatically.

## Monitoring endpoints

### `POST /api/monitor/run-check`

Runs one complete monitoring cycle across every configured service.

Each check records:

- service
- timestamp
- ONLINE / OFFLINE state
- simulated HTTP status
- response latency

### `GET /api/checks?limit=50`

Returns recent monitoring history.

The maximum limit is 500.

## Incident endpoints

### `GET /api/incidents`

Returns incident history.

Optional query:

```text
?status=ACTIVE
?status=RESOLVED
```

### `GET /api/incidents/{incident_id}/events`

Returns the event timeline for one incident.

Event types can include:

- `CREATED`
- `FAILURE_CHECK`
- `RECOVERY`
- `HELPDESK_TICKET_CREATED`
- `HELPDESK_SYNC_FAILED`

## Metrics endpoint

### `GET /api/metrics`

Returns service-level operational metrics:

- uptime percentage
- average latency
- maximum latency
- outage count
- longest outage
- last successful check

## Dashboard endpoint

### `GET /api/dashboard`

Returns one combined payload for the backend-connected frontend:

- current summary
- service cards
- incident history
- recent monitoring checks

## Demo reset

### `POST /api/reset`

Clears monitoring checks, incidents and incident events, then restores every service to ONLINE.

## Failure threshold

The default threshold is three consecutive failures:

```text
Failure 1 → no incident
Failure 2 → no incident
Failure 3 → ACTIVE incident created
```

Configure with:

```text
FAILURE_THRESHOLD=3
```

## Optional Project 1 integration

When enabled, a newly created monitoring incident can call the AI Helpdesk Copilot ticket API.

Environment:

```text
HELPDESK_INTEGRATION_ENABLED=true
HELPDESK_API_URL=http://127.0.0.1:8001
```

The integration is best-effort: an unavailable Helpdesk API never stops the monitoring worker. A failed integration attempt is recorded as an incident event instead.
