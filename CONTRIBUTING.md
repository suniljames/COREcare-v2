# COREcare v2 — Developer Guide

Multi-tenant SaaS platform for home care coordination. Ground-up rebuild with FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk + Claude API.

> **For everyone.** This file is the universal entry point for all developers — human, Claude Code, Gemini, or any future agent. Read this first, then read your agent-specific file if applicable.

## Directives

This project follows the engineering directives at [`suniljames/directives`](https://github.com/suniljames/directives). Read them for:
- [Team structure & personas](https://github.com/suniljames/directives/blob/main/process/committee-process.md)
- [Pipeline & workflow](https://github.com/suniljames/directives/blob/main/process/pipeline.md)
- [Agent architecture](https://github.com/suniljames/directives/blob/main/process/agent-architecture.md)
- [Safety guardrails](https://github.com/suniljames/directives/blob/main/process/safety.md)
- [Code review framework](https://github.com/suniljames/directives/blob/main/process/code-review-framework.md)
- [Test budget policy](https://github.com/suniljames/directives/blob/main/process/test-budget.md)
- [PRD template](https://github.com/suniljames/directives/blob/main/process/prd-template.md)
- [Healthcare overlay](https://github.com/suniljames/directives/blob/main/overlays/healthcare/) (HIPAA, PHI handling)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12, uv) |
| Frontend | Next.js 15 App Router (pnpm) |
| UI Library | shadcn/ui + Tailwind CSS |
| Database | PostgreSQL 16 + SQLModel + Alembic |
| Multi-tenancy | PostgreSQL Row-Level Security (RLS) |
| Auth | Clerk (JWT backend + React components) |
| AI | Claude API (Anthropic SDK) |
| Deployment | Docker Compose (local Mac Mini only) |
| CI | GitHub Actions |

## Dev/Test Environment

Local Docker Compose: `docker compose up` starts API (8000), Web (3000), PostgreSQL, Redis.

Test accounts (seeded by `make api-seed`):

| Role | Email | Password |
|------|-------|----------|
| Super-Admin | superadmin@test.com | `TestSuper123!` |
| Agency Admin | admin@test.com | `TestAdmin123!` |
| Care Manager | manager1@test.com | `TestManager123!` |
| Caregiver 1 | caregiver1@test.com | `TestCare123!` |
| Caregiver 2 | caregiver2@test.com | `TestCare123!` |
| Family 1 | family1@test.com | `TestFamily123!` |
| Family 2 | family2@test.com | `TestFamily123!` |

## Project Docs

| Topic | File |
|-------|------|
| Access & credentials | [`docs/developer/SETUP.md`](docs/developer/SETUP.md) |
| Architecture & patterns | [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) |
| Testing guide | [`docs/developer/TESTING.md`](docs/developer/TESTING.md) |
| Safety (project-specific) | [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) |
| Code review lenses | [`docs/developer/code-review-lenses.md`](docs/developer/code-review-lenses.md) |
| Project context | [`docs/developer/project-context.md`](docs/developer/project-context.md) |
| Design system | [`docs/design-system/`](docs/design-system/) |
| ADRs | [`docs/adr/`](docs/adr/) |

## Agent-Specific Config

| Agent | File |
|-------|------|
| Claude Code | [`CLAUDE.md`](CLAUDE.md) |
| Gemini | [`GEMINI.md`](GEMINI.md) |

## GitHub Identity

All developers (human and AI) operate as `suniljames`. See [`docs/developer/SETUP.md`](docs/developer/SETUP.md) for access setup.

## Deployment

**Local only.** Docker Compose on Mac Mini. No cloud hosting.

```bash
docker compose up --build -d && curl http://localhost:8000/healthz
```

Tailscale for network access from other devices.
