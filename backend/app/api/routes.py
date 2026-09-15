from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from ..config import FAILURE_THRESHOLD
from ..db import get_db
from ..models import Incident, IncidentEvent, MonitoredService, MonitoringCheck
from ..services.monitor import perform_check, run_monitor_cycle

router = APIRouter()


def _service_or_404(db: Session, slug: str) -> MonitoredService:
    service = db.scalar(select(MonitoredService).where(MonitoredService.slug == slug))
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


def _incident_dict(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "incident_number": incident.incident_number,
        "service": incident.service.name,
        "service_slug": incident.service.slug,
        "status": incident.status,
        "opened_at": incident.opened_at,
        "resolved_at": incident.resolved_at,
        "duration_seconds": incident.duration_seconds,
        "trigger_reason": incident.trigger_reason,
    }


def _check_dict(check: MonitoringCheck) -> dict:
    return {
        "id": check.id,
        "service": check.service.name,
        "service_slug": check.service.slug,
        "checked_at": check.checked_at,
        "online": check.online,
        "status": check.status,
        "latency_ms": check.latency_ms,
        "http_status": check.http_status,
    }


@router.get("/api/services")
def list_services(db: Session = Depends(get_db)):
    services = db.scalars(select(MonitoredService).order_by(MonitoredService.id)).all()
    return [
        {
            "id": s.id,
            "slug": s.slug,
            "name": s.name,
            "description": s.description,
            "simulated_online": s.simulated_online,
            "failure_streak": s.failure_streak,
        }
        for s in services
    ]


@router.get("/services/{slug}/health")
def service_health(slug: str, response: Response, db: Session = Depends(get_db)):
    service = _service_or_404(db, slug)
    if not service.simulated_online:
        response.status_code = 503
        return {"service": service.name, "status": "OFFLINE", "code": 503}
    return {"service": service.name, "status": "ONLINE", "code": 200}


@router.post("/api/services/{slug}/simulate-failure")
def simulate_failure(slug: str, db: Session = Depends(get_db)):
    service = _service_or_404(db, slug)
    service.simulated_online = False
    service.failure_streak = 0
    db.commit()
    return {
        "message": f"{service.name} is now simulating an outage.",
        "failure_threshold": FAILURE_THRESHOLD,
    }


@router.post("/api/services/{slug}/restore")
def restore_service(slug: str, db: Session = Depends(get_db)):
    service = _service_or_404(db, slug)
    service.simulated_online = True
    db.commit()
    check = perform_check(db, service)
    return {
        "message": f"{service.name} restored.",
        "check": _check_dict(check),
    }


@router.post("/api/monitor/run-check")
def manual_check(db: Session = Depends(get_db)):
    checks = run_monitor_cycle(db)
    return {
        "message": "Monitoring cycle completed.",
        "checks": [_check_dict(c) for c in checks],
    }


@router.get("/api/checks")
def get_checks(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)):
    checks = db.scalars(
        select(MonitoringCheck)
        .order_by(desc(MonitoringCheck.checked_at))
        .limit(limit)
    ).all()
    return [_check_dict(check) for check in checks]


@router.get("/api/incidents")
def get_incidents(status: str | None = None, db: Session = Depends(get_db)):
    statement = select(Incident).order_by(desc(Incident.opened_at))
    if status:
        statement = statement.where(Incident.status == status.upper())
    incidents = db.scalars(statement).all()
    return [_incident_dict(incident) for incident in incidents]


@router.get("/api/incidents/{incident_id}/events")
def get_incident_events(incident_id: int, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    events = db.scalars(
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at)
    ).all()
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "message": event.message,
            "created_at": event.created_at,
        }
        for event in events
    ]


@router.get("/api/metrics")
def metrics(db: Session = Depends(get_db)):
    services = db.scalars(select(MonitoredService).order_by(MonitoredService.id)).all()
    result = []

    for service in services:
        total_checks = db.scalar(
            select(func.count())
            .select_from(MonitoringCheck)
            .where(MonitoringCheck.service_id == service.id)
        ) or 0

        successful_checks = db.scalar(
            select(func.count())
            .select_from(MonitoringCheck)
            .where(
                MonitoringCheck.service_id == service.id,
                MonitoringCheck.online.is_(True),
            )
        ) or 0

        avg_latency = db.scalar(
            select(func.avg(MonitoringCheck.latency_ms))
            .where(MonitoringCheck.service_id == service.id)
        )
        max_latency = db.scalar(
            select(func.max(MonitoringCheck.latency_ms))
            .where(MonitoringCheck.service_id == service.id)
        )
        incident_count = db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(Incident.service_id == service.id)
        ) or 0
        longest_outage = db.scalar(
            select(func.max(Incident.duration_seconds))
            .where(Incident.service_id == service.id)
        )
        last_success = db.scalar(
            select(func.max(MonitoringCheck.checked_at))
            .where(
                MonitoringCheck.service_id == service.id,
                MonitoringCheck.online.is_(True),
            )
        )

        result.append(
            {
                "service": service.name,
                "service_slug": service.slug,
                "uptime_percentage": round((successful_checks / total_checks * 100), 2) if total_checks else 100.0,
                "average_latency_ms": round(float(avg_latency or 0), 2),
                "maximum_latency_ms": round(float(max_latency or 0), 2),
                "outage_count": int(incident_count),
                "longest_outage_seconds": round(float(longest_outage or 0), 2),
                "last_successful_check": last_success,
            }
        )

    return result


@router.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    services = db.scalars(select(MonitoredService).order_by(MonitoredService.id)).all()
    active_incidents = db.scalar(
        select(func.count())
        .select_from(Incident)
        .where(Incident.status == "ACTIVE")
    ) or 0
    recent_incidents = db.scalars(
        select(Incident).order_by(desc(Incident.opened_at)).limit(10)
    ).all()
    recent_checks = db.scalars(
        select(MonitoringCheck)
        .order_by(desc(MonitoringCheck.checked_at))
        .limit(60)
    ).all()

    service_rows = []
    for service in services:
        latest = db.scalar(
            select(MonitoringCheck)
            .where(MonitoringCheck.service_id == service.id)
            .order_by(desc(MonitoringCheck.checked_at))
            .limit(1)
        )
        service_rows.append(
            {
                "slug": service.slug,
                "name": service.name,
                "description": service.description,
                "status": latest.status if latest else ("ONLINE" if service.simulated_online else "OFFLINE"),
                "latency_ms": latest.latency_ms if latest else 0,
                "failure_streak": service.failure_streak,
                "threshold": FAILURE_THRESHOLD,
            }
        )

    latencies = [c.latency_ms for c in recent_checks if c.online]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0
    online_services = sum(1 for s in service_rows if s["status"] == "ONLINE")

    return {
        "generated_at": datetime.now(UTC),
        "summary": {
            "online_services": online_services,
            "offline_services": len(service_rows) - online_services,
            "active_incidents": int(active_incidents),
            "average_latency_ms": avg_latency,
        },
        "services": service_rows,
        "incidents": [_incident_dict(i) for i in recent_incidents],
        "recent_checks": [_check_dict(c) for c in recent_checks],
    }


@router.post("/api/reset")
def reset_demo(db: Session = Depends(get_db)):
    db.query(IncidentEvent).delete()
    db.query(Incident).delete()
    db.query(MonitoringCheck).delete()

    for service in db.scalars(select(MonitoredService)).all():
        service.simulated_online = True
        service.failure_streak = 0

    db.commit()
    return {
        "message": "Demo monitoring data and incidents reset. All services are online."
    }
