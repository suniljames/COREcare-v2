# ADR-007: Event-Sourced Audit Logging

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-002 (RLS), ADR-006 (AI)

## Context

HIPAA requires comprehensive audit trails for all access to Protected Health Information (PHI). We need to track who accessed what, when, why, and from where. Standard application logging is insufficient — we need structured, queryable, tamper-evident audit records.

## Decision

Implement **event-sourced audit logging** with a dedicated `audit_events` table.

### Event Structure
```
AuditEvent:
  id: UUID
  timestamp: datetime (UTC)
  actor_id: UUID (who)
  actor_role: string
  agency_id: UUID (tenant context)
  action: string (read, create, update, delete, login, impersonate, export)
  resource_type: string (client, visit, chart, user, etc.)
  resource_id: UUID
  details: JSONB (action-specific metadata, NO PHI)
  ip_address: string
  user_agent: string
```

### Categories
1. **Security events** — login, logout, failed auth, role changes, impersonation
2. **PHI access** — any read/write to client records, charts, visit notes
3. **Operational events** — CRUD on non-PHI resources, system actions
4. **AI events** — model invocations, prompt/response metadata (no content)

### Implementation
- Async audit service — non-blocking writes
- Decorator/middleware for automatic logging
- Append-only table (no updates or deletes)
- Super-admin query API for audit trail review
- Retention: minimum 6 years (HIPAA requirement)

## Consequences

### Positive
- HIPAA-compliant audit trail
- Queryable history for compliance reviews
- Security incident investigation capability
- Append-only design prevents tampering

### Negative
- Storage growth over time (mitigate with partitioning by month)
- Write amplification (every data access generates an audit event)
- Query complexity for audit trail analysis

### Risks
- Audit table becoming a performance bottleneck — mitigate with async writes and table partitioning
- PHI accidentally included in audit event details — mitigate with strict schema validation on the JSONB details field
