# Case Study — Network Monitoring & Incident System

## Problem

Operational teams need to know when important services become unavailable, but creating an incident on every single failed check produces alert noise and false positives.

This project models a small monitoring platform that distinguishes between a temporary failure and a persistent outage.

## Goal

Build a recruiter-facing project that demonstrates practical understanding of:

- service availability monitoring
- health checks
- latency tracking
- repeated-failure logic
- automated incident creation
- recovery handling
- uptime and outage metrics
- operational dashboards
- backend APIs
- persistent data models
- automated testing

## Solution

The system monitors five simulated services:

- Web Server
- API Server
- Database Service
- Authentication Service
- File Service

A monitoring cycle records a status and latency observation for each service.

The key reliability rule is:

```text
Check 1 fails → record failure
Check 2 fails → record failure
Check 3 fails → create incident
```

This avoids treating one isolated failure as a confirmed outage.

When the service returns online:

```text
Recovery check succeeds
→ active incident resolved
→ resolved timestamp stored
→ outage duration calculated
→ recovery event added to incident timeline
```

## Two portfolio experiences

### 1. Full engineering repository

The repository contains the actual implementation:

- Python / FastAPI
- SQLAlchemy data model
- SQLite for easy local testing
- PostgreSQL-ready production configuration
- Docker Compose
- background monitoring worker
- incident lifecycle engine
- operational metrics
- real backend-connected frontend
- pytest test suite
- GitHub Actions CI
- optional AI Helpdesk Copilot integration

### 2. GitHub Pages recruiter demo

The static live demo runs entirely in the browser.

It intentionally reproduces the same business rules without pretending that GitHub Pages hosts Python or PostgreSQL.

A recruiter can:

1. choose a service
2. simulate an outage
3. run health checks
4. watch the failure counter reach 3
5. see an incident created
6. restore the service
7. watch the incident resolve
8. inspect logs and charts

## Why use a separate static demo?

GitHub Pages hosts static files and cannot run a FastAPI/PostgreSQL application.

For portfolio reliability, the public demo should:

- open instantly
- require no account
- avoid backend sleep/cold-start delays
- never depend on external services
- remain safe for repeated recruiter testing

The repository therefore separates **demonstration** from **server-side implementation**.

## Data model

### monitored_services

Stores service identity and current simulated monitoring state.

### monitoring_checks

Stores timestamped health observations:

- online status
- HTTP result
- latency

### incidents

Stores outage lifecycle:

- incident number
- service
- ACTIVE / RESOLVED status
- opened time
- resolved time
- duration
- trigger reason

### incident_events

Stores an auditable timeline of incident events.

## Optional cross-project workflow

Project 3 can integrate with Project 1:

```text
Service outage
→ 3 failed checks
→ monitoring incident created
→ AI Helpdesk Copilot API called
→ support ticket created
```

This demonstrates service-to-service API integration across two portfolio projects.

## Engineering decisions

### Repeated failure threshold

Three failures were chosen as the default to demonstrate noise reduction. The value is configurable.

### Safe simulation

The portfolio demo only monitors simulated infrastructure so recruiters can trigger outages safely.

### SQLite + PostgreSQL

SQLite reduces local setup friction. PostgreSQL is available through Docker Compose for a production-style stack.

### Best-effort external integration

The monitoring platform must continue working even if the Helpdesk API is unavailable. Integration failures are recorded but do not crash monitoring.

## Recruiter takeaway

The project demonstrates more than a dashboard. It shows an end-to-end operational workflow:

```text
monitor → detect → confirm → incident → recover → resolve → measure
```

That flow is directly relevant to IT support, service desk, infrastructure, backend and junior DevOps / operations-oriented roles.
