# Reviewing and running the incident monitor

## Simulation boundary

Both the browser demo and the backend operate on simulated services. In the backend, `perform_check` reads `simulated_online` and generates latency with `random.uniform`; it does not send HTTP probes to real external targets. The project demonstrates repeated-failure and recovery logic. Its availability and latency numbers are not measurements of a real network.

## Local setup

Python 3.14 matches the repository CI configuration. From a fresh clone:

```powershell
git clone https://github.com/Billalhossainshishir/network-monitoring-incident-system.git
cd network-monitoring-incident-system
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

In another terminal at the repository root:

```powershell
py -3.14 -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500`; inspect the API at `http://127.0.0.1:8000/docs`. The API root returns service information, not the dashboard.

Docker Compose runs PostgreSQL and the API. It does not run a frontend container. After `docker compose up --build`, use the same separate frontend command above.

## Configuration

The Python code uses `os.getenv`; it does not automatically read `.env.example` or `.env`. Set variables in the shell that starts Uvicorn, or put them explicitly in the Compose service environment. For a repeatable manual incident experiment:

```powershell
$env:DISABLE_BACKGROUND_MONITOR='true'
$env:FAILURE_THRESHOLD='3'
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000
```

Stop a previously running server before restarting with different settings. With background monitoring disabled, each `/api/monitor/run-check` call represents one controlled cycle. Normal operation defaults to a two-second background interval, so manual clicks and background cycles can otherwise overlap.

## Incident walkthrough

1. In Swagger, simulate failure for service slug `api`.
2. Call `POST /api/monitor/run-check` twice; expect no active incident for that service.
3. Call it a third time; expect one ACTIVE incident.
4. Run another failed cycle; expect the existing incident, not a duplicate.
5. Restore the service and run a successful cycle if needed; inspect the RESOLVED incident and its event timeline.

The exact restore endpoint also performs a check, so check the returned state before issuing another manual cycle. Uptime is the proportion of stored successful checks, not a time-weighted SLA. Incident duration starts when the threshold creates the incident, rather than at the first failed observation.

## Optional Helpdesk integration

Start AI Helpdesk Copilot separately on port 8001. In the monitor's process environment, set:

```powershell
$env:HELPDESK_INTEGRATION_ENABLED='true'
$env:HELPDESK_API_URL='http://127.0.0.1:8001'
$env:HELPDESK_REQUESTER_EMAIL='monitor@example.com'
```

Restart the monitor and produce a new incident. Inspect its events for `HELPDESK_TICKET_CREATED` or `HELPDESK_SYNC_FAILED`. Use a valid sample requester address because the receiving API validates email addresses. Container networking requires a reachable service/host address; `127.0.0.1` inside a container refers to that container.

The existing unit/API suite covers the incident lifecycle and metrics fields. It does not establish that this cross-project integration works end to end. Run the walkthrough with both applications and retain the result before claiming a successful integrated deployment.

## Verification and limitations

Run `python -m pytest -q` using the virtual environment. The system has no real target configuration, production alert delivery or validated SLA reporting. Those are future extensions. `docker compose down -v` deletes the demonstration PostgreSQL volume; ordinary `down` preserves it.


## Recorded verification evidence

At documentation review, the existing [GitHub Actions test run](https://github.com/Billalhossainshishir/network-monitoring-incident-system/actions/runs/34967654730) reported `success` for `3208b33f1e39ba6f605420aaff24827c66f89f01`. This records an existing CI result; the documentation review did not install dependencies or rerun the application locally. Commands above were checked against source files and configuration. A successful CI run does not establish production readiness or validate untested UI integrations.
