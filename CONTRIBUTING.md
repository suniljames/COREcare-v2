# COREcare v2 — Developer Guide

Multi-tenant SaaS platform for home care coordination. Ground-up rebuild with FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk + Claude API.

This project follows the [engineering directives](https://github.com/suniljames/directives) (includes [healthcare overlay](https://github.com/suniljames/directives/blob/main/overlays/healthcare/)).

<!-- team: engineering -->
<!-- pipeline-mode: autonomous -->

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

```bash
make check        # Lint + typecheck + test + build (must pass before PRs)
make test         # All tests
make api-test     # API tests only
make web-test     # Web tests only
make test-e2e     # E2E tests (requires Docker stack)
```

Tailscale for network access from other devices.

## Project Docs

| Topic | File |
|-------|------|
| Architecture & patterns | [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) |
| Testing guide | [`docs/developer/TESTING.md`](docs/developer/TESTING.md) |
| Safety (project-specific) | [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) |
| Code review lenses | [`docs/developer/code-review-lenses.md`](docs/developer/code-review-lenses.md) |
| Project context | [`docs/developer/project-context.md`](docs/developer/project-context.md) |
| Design system | [`docs/design-system/`](docs/design-system/) |
| ADRs | [`docs/adr/`](docs/adr/) |
