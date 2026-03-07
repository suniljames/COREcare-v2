# ADR-005: Docker Compose Local Deployment

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-001 (Architecture)

## Context

COREcare v2 needs a deployment strategy. Options range from cloud platforms (AWS, Render, Vercel) to local self-hosting.

The platform owner has a Mac Mini available for hosting. The user base is currently small (single agency transitioning from v1). Cloud hosting adds cost and complexity that isn't justified at this stage.

## Decision

Deploy locally via **Docker Compose on Mac Mini**. No cloud hosting.

### Services
- `api` — FastAPI (Python 3.12)
- `web` — Next.js 15 (Node 20)
- `db` — PostgreSQL 16
- `redis` — Redis 7 (sessions, caching, job queue)

### Access
- Local network: `http://mac-mini-hostname:3000` (web), `:8000` (API)
- Remote access: Tailscale for secure access from anywhere
- No public internet exposure required

## Consequences

### Positive
- Zero hosting costs
- Full control over data (HIPAA: data never leaves the premises)
- Simple deployment: `docker compose up --build -d`
- No vendor lock-in
- Easy to add cloud later if needed (services are already containerized)

### Negative
- Single point of failure (Mac Mini hardware)
- No auto-scaling
- Backup responsibility falls on the operator
- No CDN for static assets (acceptable for small user base)

### Risks
- Hardware failure — mitigate with automated backups to external storage
- Power/network outage — mitigate with UPS and Tailscale for remote monitoring
- Growth beyond Mac Mini capacity — mitigate by containerization making cloud migration straightforward
