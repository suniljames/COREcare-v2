# COREcare v2 — Developer Guide

Multi-tenant SaaS platform for home care coordination. Ground-up rebuild with FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk + Claude API.

> **For everyone.** This file is the universal entry point for all developers — human, Claude Code, Gemini, or any future agent. Read this first, then read your agent-specific file if applicable.

## Documentation Index

| Topic | File |
|-------|------|
| **Getting Started** | |
| Access & credentials setup | [`docs/developer/SETUP.md`](docs/developer/SETUP.md) |
| Project rules (mandatory) | [`docs/developer/PROJECT_RULES.md`](docs/developer/PROJECT_RULES.md) |
| **How We Work** | |
| Team structure & personas | [`docs/developer/TEAM.md`](docs/developer/TEAM.md) |
| Pipeline & workflow | [`docs/developer/PIPELINE.md`](docs/developer/PIPELINE.md) |
| Architecture & patterns | [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) |
| **Quality** | |
| Testing guide | [`docs/developer/TESTING.md`](docs/developer/TESTING.md) |
| Test layer budget | [`docs/developer/TEST_BUDGET.md`](docs/developer/TEST_BUDGET.md) |
| Safety & guardrails | [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) |
| Code review lenses | [`docs/developer/code-review-lenses.md`](docs/developer/code-review-lenses.md) |
| PRD template | [`docs/developer/prd-template.md`](docs/developer/prd-template.md) |
| **Design** | |
| Design system | [`docs/design-system/`](docs/design-system/) |
| **Decisions** | |
| ADRs | [`docs/adr/`](docs/adr/) |
| Agent split rationale | [`docs/adr/009-multi-agent-engineering-split.md`](docs/adr/009-multi-agent-engineering-split.md) |
| **Agent-Specific** | |
| Claude Code config | [`CLAUDE.md`](CLAUDE.md) |
| Gemini config | [`GEMINI.md`](GEMINI.md) |

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

## Next Steps

1. Read [`docs/developer/SETUP.md`](docs/developer/SETUP.md) to configure access.
2. Read [`docs/developer/PROJECT_RULES.md`](docs/developer/PROJECT_RULES.md) — these are mandatory.
3. If you are an AI agent, read your agent file ([`CLAUDE.md`](CLAUDE.md) or [`GEMINI.md`](GEMINI.md)).
4. Browse the documentation index above for deeper reference.
