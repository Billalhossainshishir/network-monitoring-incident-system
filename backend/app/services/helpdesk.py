import os

import httpx

HELPDESK_INTEGRATION_ENABLED = os.getenv("HELPDESK_INTEGRATION_ENABLED", "false").lower() == "true"
HELPDESK_API_URL = os.getenv("HELPDESK_API_URL", "http://127.0.0.1:8001").rstrip("/")
HELPDESK_REQUESTER_NAME = os.getenv("HELPDESK_REQUESTER_NAME", "Network Monitor")
HELPDESK_REQUESTER_EMAIL = os.getenv("HELPDESK_REQUESTER_EMAIL", "monitor@portfolio.local")


def create_helpdesk_ticket(service, incident) -> dict:
    """Best-effort Project 1 integration.

    The monitoring system remains fully functional when integration is disabled.
    When enabled, an automatically-created monitoring incident is posted to the
    AI Helpdesk Copilot ticket API. Network errors are returned as structured
    results instead of breaking the monitoring loop.
    """
    if not HELPDESK_INTEGRATION_ENABLED:
        return {"status": "disabled"}

    payload = {
        "name": HELPDESK_REQUESTER_NAME,
        "email": HELPDESK_REQUESTER_EMAIL,
        "title": f"Automatic outage incident: {service.name}",
        "description": (
            f"{service.name} generated monitoring incident {incident.incident_number}. "
            f"Reason: {incident.trigger_reason}"
        ),
        "device_type": "Infrastructure Service",
        "category": "Network",
        "priority": "High",
    }

    try:
        response = httpx.post(f"{HELPDESK_API_URL}/tickets", json=payload, timeout=3.0)
        response.raise_for_status()
        body = response.json()
        return {
            "status": "created",
            "ticket_number": body.get("ticket_number") or body.get("id"),
        }
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
