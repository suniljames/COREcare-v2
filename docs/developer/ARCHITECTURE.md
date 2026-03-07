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
