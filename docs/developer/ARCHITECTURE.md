# Architecture & Development Patterns

## Multi-Tenancy

- All data queries must be tenant-scoped via PostgreSQL Row-Level Security (RLS) policies.
- Super-admin bypasses RLS to see all agencies.
- Never expose cross-tenant data in API responses.
- Test multi-tenant isolation in service tests for every data-access endpoint.

## API Patterns (FastAPI)

- **Service layer pattern:** routers call services, services call models. No business logic in routers.
- Pydantic schemas for all request/response I/O.
- Alembic for database migrations.
- SQLModel for ORM.

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
