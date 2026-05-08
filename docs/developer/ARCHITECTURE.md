# Architecture & Development Patterns

## Multi-Tenancy

- All data queries must be tenant-scoped via PostgreSQL Row-Level Security (RLS) policies.
- Super-admin bypasses RLS to see all agencies.
- Never expose cross-tenant data in API responses.
- Test multi-tenant isolation in service tests for every data-access endpoint.

## API Patterns (FastAPI)

- **Service layer pattern:** routers call services, services call models. No business logic in routers.
- Pydantic schemas for all request/response I/O.
- SQLModel for ORM.

## Database schema

- **Source of truth:** `app.models.*` defines schema intent; `alembic upgrade head` is the contract that brings the DB to that state. Production, staging, dev, and CI all bootstrap via `make api-migrate` (then `make api-seed`).
- **Drift guard:** `api/app/tests/test_migrations_e2e.py` runs an ephemeral Postgres, applies migrations, and runs `alembic check` to assert `SQLModel.metadata` ≡ migration head. Wired into `make check`. If you change a model, regenerate the migration (`make -C api migration MSG="..."`) before pushing.
- **`SQLModel.metadata.create_all` is unit-test-only.** It is invoked from a handful of test fixtures as a fast path (skip Alembic for in-memory SQLite) but is **not** acceptable for any shared environment. Defending the equivalence between the two paths is the drift guard's only job.
- See [`docs/developer/migrations-runbook.md`](migrations-runbook.md) for bootstrap, reset, add-a-migration, and recovery flows.

## Web Patterns (Next.js 15)

- **Server Components by default.** Client Components only when interactivity is required.
- Use shadcn/ui components from the design system.
- **Shared component reuse:** Search for existing components before creating new ones.
- Follow design system tokens — no hardcoded colors, spacing, or fonts. See [`docs/design-system/`](../design-system/).

## Auth

- Clerk handles authentication: JWT verification on the backend, React components on the frontend.
- Backend validates Clerk JWTs and extracts tenant context for RLS.

## Outbound communications

- All outbound email passes through `app.services.email.EmailSender`. Per-feature email methods (e.g., `BillingService.email_invoice`) call the sender; no feature service or router instantiates a transport directly.
- Every send produces one row in `email_events` (single audit table, RLS-scoped). The architecture-fitness test in `api/app/tests/architecture/test_email_boundary.py` hard-fails CI if any module outside `app.services.email.*` imports a transport SDK.
- See [`ADR-011`](../adr/011-email-outbound-boundary.md) for the full contract.
