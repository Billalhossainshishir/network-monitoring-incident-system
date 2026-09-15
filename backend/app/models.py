from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utc_now():
    return datetime.now(UTC).replace(tzinfo=None)


class MonitoredService(Base):
    __tablename__ = "monitored_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255))
    simulated_online: Mapped[bool] = mapped_column(Boolean, default=True)
    failure_streak: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    checks = relationship("MonitoringCheck", back_populates="service", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="service", cascade="all, delete-orphan")


class MonitoringCheck(Base):
    __tablename__ = "monitoring_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("monitored_services.id"), index=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    online: Mapped[bool] = mapped_column(Boolean)
    status: Mapped[str] = mapped_column(String(20))
    latency_ms: Mapped[float] = mapped_column(Float)
    http_status: Mapped[int] = mapped_column(Integer)

    service = relationship("MonitoredService", back_populates="checks")


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("monitored_services.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    trigger_reason: Mapped[str] = mapped_column(Text)

    service = relationship("MonitoredService", back_populates="incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    incident = relationship("Incident", back_populates="events")
