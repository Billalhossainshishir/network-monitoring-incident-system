import random
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import FAILURE_THRESHOLD
from ..models import Incident, IncidentEvent, MonitoredService, MonitoringCheck


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)


SERVICE_SEED = [
    ("web", "Web Server", "Public-facing website service"),
    ("api", "API Server", "Core application API service"),
    ("database", "Database Service", "Primary application database"),
    ("auth", "Authentication Service", "Identity and login service"),
    ("file", "File Service", "Document and file storage service"),
]


def seed_services(db: Session) -> None:
    existing = {row.slug for row in db.scalars(select(MonitoredService)).all()}
    for slug, name, description in SERVICE_SEED:
        if slug not in existing:
            db.add(MonitoredService(slug=slug, name=name, description=description))
    db.commit()


def _active_incident(db: Session, service_id: int) -> Incident | None:
    return db.scalar(
        select(Incident)
        .where(Incident.service_id == service_id, Incident.status == "ACTIVE")
        .order_by(desc(Incident.opened_at))
    )


def _incident_number(service: MonitoredService) -> str:
    stamp = utc_now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    return f"INC-{service.slug.upper()}-{stamp}"


def perform_check(db: Session, service: MonitoredService) -> MonitoringCheck:
    now = utc_now()
    if service.simulated_online:
        latency = round(random.uniform(18, 145), 2)
        check = MonitoringCheck(
            service_id=service.id,
            checked_at=now,
            online=True,
            status="ONLINE",
            latency_ms=latency,
            http_status=200,
        )
        service.failure_streak = 0
        incident = _active_incident(db, service.id)
        if incident:
            incident.status = "RESOLVED"
            incident.resolved_at = now
            incident.duration_seconds = round((now - incident.opened_at).total_seconds(), 2)
            db.add(
                IncidentEvent(
                    incident_id=incident.id,
                    event_type="RECOVERY",
                    message=f"{service.name} recovered and the incident was resolved automatically.",
                    created_at=now,
                )
            )
    else:
        latency = round(random.uniform(900, 1800), 2)
        check = MonitoringCheck(
            service_id=service.id,
            checked_at=now,
            online=False,
            status="OFFLINE",
            latency_ms=latency,
            http_status=503,
        )
        service.failure_streak += 1
        incident = _active_incident(db, service.id)
        if service.failure_streak >= FAILURE_THRESHOLD and not incident:
            incident = Incident(
                incident_number=_incident_number(service),
                service_id=service.id,
                status="ACTIVE",
                opened_at=now,
                trigger_reason=f"{FAILURE_THRESHOLD} consecutive health-check failures detected.",
            )
            db.add(incident)
            db.flush()
            db.add(
                IncidentEvent(
                    incident_id=incident.id,
                    event_type="CREATED",
                    message=f"Incident created after {service.failure_streak} consecutive failures.",
                    created_at=now,
                )
            )
        elif incident:
            db.add(
                IncidentEvent(
                    incident_id=incident.id,
                    event_type="FAILURE_CHECK",
                    message=f"Additional failed check recorded. Failure streak: {service.failure_streak}.",
                    created_at=now,
                )
            )

    db.add(check)
    db.add(service)
    db.commit()
    db.refresh(check)
    return check


def run_monitor_cycle(db: Session) -> list[MonitoringCheck]:
    services = db.scalars(select(MonitoredService).order_by(MonitoredService.id)).all()
    return [perform_check(db, service) for service in services]
