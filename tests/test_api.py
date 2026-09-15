import os
from pathlib import Path

TEST_DB = Path("test_network_monitor.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["DISABLE_BACKGROUND_MONITOR"] = "true"
os.environ["FAILURE_THRESHOLD"] = "3"
os.environ["HELPDESK_INTEGRATION_ENABLED"] = "false"

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_and_seeded_services():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        services = client.get("/api/services").json()
        assert len(services) == 5
        assert {s["slug"] for s in services} == {"web", "api", "database", "auth", "file"}


def test_simulated_service_health_endpoint_changes_status():
    with TestClient(app) as client:
        client.post("/api/reset")

        online = client.get("/services/api/health")
        assert online.status_code == 200
        assert online.json()["status"] == "ONLINE"

        client.post("/api/services/api/simulate-failure")
        offline = client.get("/services/api/health")
        assert offline.status_code == 503
        assert offline.json()["status"] == "OFFLINE"


def test_no_incident_before_failure_threshold():
    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/services/api/simulate-failure")

        client.post("/api/monitor/run-check")
        assert client.get("/api/incidents?status=ACTIVE").json() == []

        client.post("/api/monitor/run-check")
        assert client.get("/api/incidents?status=ACTIVE").json() == []


def test_three_failures_create_incident_and_restore_resolves_it():
    with TestClient(app) as client:
        client.post("/api/reset")
        assert client.post("/api/services/api/simulate-failure").status_code == 200

        for _ in range(3):
            response = client.post("/api/monitor/run-check")
            assert response.status_code == 200

        incidents = client.get("/api/incidents?status=ACTIVE").json()
        api_incidents = [i for i in incidents if i["service_slug"] == "api"]
        assert len(api_incidents) == 1
        assert api_incidents[0]["status"] == "ACTIVE"

        restore = client.post("/api/services/api/restore")
        assert restore.status_code == 200

        resolved = client.get("/api/incidents?status=RESOLVED").json()
        api_resolved = [i for i in resolved if i["service_slug"] == "api"]
        assert len(api_resolved) == 1
        assert api_resolved[0]["resolved_at"] is not None
        assert api_resolved[0]["duration_seconds"] is not None


def test_continued_failures_do_not_create_duplicate_active_incidents():
    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/services/database/simulate-failure")

        for _ in range(6):
            client.post("/api/monitor/run-check")

        active = client.get("/api/incidents?status=ACTIVE").json()
        database_incidents = [i for i in active if i["service_slug"] == "database"]
        assert len(database_incidents) == 1


def test_incident_event_timeline_contains_creation_and_recovery():
    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/services/auth/simulate-failure")

        for _ in range(3):
            client.post("/api/monitor/run-check")

        incident = [
            i for i in client.get("/api/incidents?status=ACTIVE").json()
            if i["service_slug"] == "auth"
        ][0]

        events = client.get(f"/api/incidents/{incident['id']}/events").json()
        assert any(event["event_type"] == "CREATED" for event in events)

        client.post("/api/services/auth/restore")

        events = client.get(f"/api/incidents/{incident['id']}/events").json()
        assert any(event["event_type"] == "RECOVERY" for event in events)


def test_dashboard_returns_expected_sections():
    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/monitor/run-check")

        response = client.get("/api/dashboard")
        assert response.status_code == 200

        body = response.json()
        assert {"generated_at", "summary", "services", "incidents", "recent_checks"}.issubset(body)
        assert len(body["services"]) == 5


def test_metrics_return_operational_fields():
    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/monitor/run-check")
        metrics = client.get("/api/metrics")
        assert metrics.status_code == 200
        row = metrics.json()[0]
        expected = {
            "uptime_percentage",
            "average_latency_ms",
            "maximum_latency_ms",
            "outage_count",
            "longest_outage_seconds",
            "last_successful_check",
        }
        assert expected.issubset(row)


def test_reset_clears_incidents_and_restores_services():
    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/services/file/simulate-failure")
        for _ in range(3):
            client.post("/api/monitor/run-check")

        assert client.get("/api/incidents").json()

        reset = client.post("/api/reset")
        assert reset.status_code == 200
        assert client.get("/api/incidents").json() == []
        assert client.get("/api/checks").json() == []

        services = client.get("/api/services").json()
        assert all(service["simulated_online"] for service in services)
        assert all(service["failure_streak"] == 0 for service in services)


def teardown_module():
    if TEST_DB.exists():
        TEST_DB.unlink()
