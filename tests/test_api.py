import os
from pathlib import Path

TEST_DB = Path("test_network_monitor.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["DISABLE_BACKGROUND_MONITOR"] = "true"
os.environ["FAILURE_THRESHOLD"] = "3"

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_and_seeded_services():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        services = client.get("/api/services").json()
        assert len(services) == 5
        assert {s["slug"] for s in services} == {"web", "api", "database", "auth", "file"}


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


def teardown_module():
    if TEST_DB.exists():
        TEST_DB.unlink()
