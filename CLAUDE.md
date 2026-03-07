# COREcare v2 Project Guidelines

Multi-tenant SaaS platform for home care coordination. Ground-up rebuild with FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk + Claude API.

## Documentation Index

| Topic | File | Description |
|-------|------|-------------|
| Personas | See `.claude/docs/PERSONAS.md` | Hazel interaction guide |
| Engineering Committee | See `docs/developer/ENGINEERING_COMMITTEE.md` | Committee review process |
| Workflow | See `.claude/docs/WORKFLOW.md` | Fully autonomous issue lifecycle |
| Safety & Guardrails | See `.claude/docs/SAFETY.md` | Destructive action prohibitions |
| Testing | See `docs/developer/TESTING.md` | pytest/vitest/Playwright guides |
| Test Budget | See `docs/developer/TEST_BUDGET.md` | Layer decision checklist |
| Design System | See `docs/design-system/` | Brand, tokens, components, responsive, a11y |

---

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

---

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

---

## Critical Rules (Always Apply)

### GitHub Identity
- **All GitHub operations must be performed as `suniljames`.**
- Before any `gh` CLI command, run `gh auth switch --user suniljames`.
- Git commits use `suniljames <suniljames@users.noreply.github.com>`.

### Fully Autonomous Workflow
- **No human review gates.** Claude Code fills every role: PM, UX Designer, Software Engineer, System Architect, Data Engineer, AI/ML Engineer, Security Engineer, QA Engineer, SRE, Tech Writer, and the Engineering Manager.
- Product questions are resolved by the PM persona inline.
- Engineering questions are resolved by the Engineering Manager (convening the committee if needed).
- The full `/pm` -> `/design` -> `/implement` -> `/ramd` pipeline runs without stopping.
- PRs are squash-merged autonomously after code review passes.

### Data Verification
- **Never report data loss without full verification.**
- Dashboard counts != database counts (dashboards show filtered views).
- Express uncertainty first: "Let me verify further before drawing conclusions."

### Multi-Tenancy
- All data queries must be tenant-scoped via RLS policies.
- Super-admin bypasses RLS to see all agencies.
- Never expose cross-tenant data in API responses.
- Test multi-tenant isolation in service tests for every data-access endpoint.

### Development Patterns
- **API:** Service layer pattern — routers call services, services call models. No business logic in routers.
- **Web:** Server Components by default. Client Components only for interactivity. Use shadcn/ui components.
- **Shared component reuse:** Search for existing components before creating new ones.
- Follow design system tokens — no hardcoded colors, spacing, or fonts.

### Testing & Quality Gates
- TDD: Write failing tests first, then implement.
- `make check` must pass before any PR (runs all linters + tests + typecheck + build).
- CI runs against PostgreSQL 16.
- See `docs/developer/TESTING.md` for backend/frontend test guides.

### Session Isolation
- **Every code change must be associated with a GitHub issue.**
- **The main checkout must stay on `main`.** All feature work happens in worktrees.
- Use `claude -w` or `EnterWorktree` for isolation.
- Resume with `claude --from-pr <url>`.

### Deployment
- **Local only.** Docker Compose on Mac Mini. No cloud hosting.
- `docker compose up --build -d && curl http://localhost:8000/healthz`
- Tailscale for network access from other devices.

### For Hazel
- Always ask "Who is this?" at the start of a conversation.
- If Hazel, follow guidance in `.claude/docs/PERSONAS.md`.
