# ADR-002: PostgreSQL RLS for Multi-Tenancy

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-001 (Architecture), ADR-005 (Deployment), ADR-007 (Audit)

## Context

COREcare v2 serves multiple home care agencies on a single platform. Each agency's data must be strictly isolated — a caregiver at Agency A must never see Agency B's clients or schedules. This is a HIPAA requirement.

Three common multi-tenancy approaches:

1. **Separate databases** — strongest isolation, hardest to manage (migrations, connections)
2. **Schema-per-tenant** — good isolation, but PostgreSQL schema management is complex at scale
3. **Shared tables with Row-Level Security (RLS)** — single schema, database-enforced isolation

## Decision

Use **PostgreSQL Row-Level Security (RLS)** on all tenant-scoped tables.

### Mechanism
- Every tenant-scoped table includes an `agency_id` column
- RLS policies filter rows based on `current_setting('app.current_tenant_id')`
- The FastAPI middleware sets this session variable from the authenticated user's agency
- Super-admin bypasses RLS via `SET ROLE` or a separate connection without RLS enabled

### Implementation
```sql
-- Example RLS policy
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON clients
  USING (agency_id = current_setting('app.current_tenant_id')::uuid);
```

- A `TenantScopedModel` base class auto-includes `agency_id` and the FK relationship
- Middleware sets `app.current_tenant_id` at the start of each request
- Super-admin operations use a session that bypasses RLS (`SET LOCAL ROLE superadmin`)

## Consequences

### Positive
- **Database-enforced isolation** — bugs in application code can't leak data across tenants
- **Single schema** — one set of Alembic migrations for all tenants
- **Query simplicity** — application code doesn't need `WHERE agency_id = ?` on every query
- **Performance** — PostgreSQL optimizes RLS policies efficiently with proper indexes
- **HIPAA compliance** — strongest possible isolation at the data layer

### Negative
- **RLS complexity** — policies must be maintained as the schema evolves
- **Testing overhead** — must test with multiple tenants to verify isolation
- **Super-admin escape hatch** — bypassing RLS requires careful audit logging (see ADR-007)
- **Migration care** — new tables must have RLS policies applied; easy to forget

### Risks
- Forgetting to apply RLS to a new table — mitigate with a CI check that verifies all `TenantScopedModel` subclasses have RLS policies
- Super-admin bypass misuse — mitigate with audit logging on all super-admin operations
