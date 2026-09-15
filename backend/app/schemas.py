from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    description: str
    simulated_online: bool
    failure_streak: int


class CheckOut(BaseModel):
    id: int
    service: str
    checked_at: datetime
    online: bool
    status: str
    latency_ms: float
    http_status: int


class IncidentOut(BaseModel):
    id: int
    incident_number: str
    service: str
    status: str
    opened_at: datetime
    resolved_at: datetime | None
    duration_seconds: float | None
    trigger_reason: str


class DashboardOut(BaseModel):
    generated_at: datetime
    summary: dict
    services: list[dict]
    incidents: list[dict]
    recent_checks: list[dict]
