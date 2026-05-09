# Glossary

Canonical definitions for terms that show up across the COREcare codebase and docs. If you're new to home-care SaaS or to this product, skim this once.

> **Other glossaries:** [`docs/migration/v1-glossary.md`](migration/v1-glossary.md) covers v1-specific model and feature names you only need when porting v1 behavior to v2. [`.claude/pm-context.md`](../.claude/pm-context.md) carries product / persona / compliance context for AI agents. The definitions below are the canonical source for the shared product vocabulary; the other files defer here.

## Domain terms

| Term | Definition |
|------|-----------|
| **Agency** | A home-care business that employs caregivers and serves clients. Each agency is a tenant. |
| **Tenant** | An agency and all its associated data, isolated by PostgreSQL Row-Level Security (RLS). One tenant per agency. |
| **Client** | The person receiving home-care services (often elderly or disabled). In v2, Clients can optionally have a User record and log in (the "Client persona" — shipped in [#125](https://github.com/suniljames/COREcare-v2/issues/125)). |
| **Caregiver** | Field worker (RN, CNA, HHA, therapist) who provides direct care in client homes. Highest-volume, lowest-patience user — UX defaults to their mobile experience. |
| **Care Manager** | Supervising nurse or coordinator who creates care plans and oversees caregiver assignments. |
| **Family Member** | A client's relative or authorized representative with limited platform visibility. Linked to a Client via `ClientFamilyMember`. |
| **Agency Admin** | Agency-level manager handling scheduling, compliance, billing, and oversight inside a single tenant. |
| **Super-Admin** | Platform operator who can see across all agencies (bypasses RLS). Forward-looking in v2; v1 has no Super-Admin role. |
| **Care Plan** | Structured document defining a client's care needs, goals, interventions, and schedule. |
| **Visit** | A scheduled caregiver-client interaction with clock-in/out, tasks, and documentation. |
| **Shift** | A time block during which a caregiver is assigned to a client. |

## Compliance and architecture terms

| Term | Definition |
|------|-----------|
| **PHI** | Protected Health Information — any individually identifiable health data. HIPAA-regulated. Never appears in logs, errors, URLs, or analytics. See [`docs/developer/SAFETY.md`](developer/SAFETY.md). |
| **RLS** | PostgreSQL Row-Level Security. The mechanism that enforces tenant isolation: queries automatically filter to the calling user's `agency_id` regardless of what the application code asks for. See [ADR-002](adr/002-postgresql-rls-multi-tenancy.md). |
| <a id="rls-bypass-surface"></a>**RLS-bypass surface** | Routes that intentionally cross tenant boundaries (e.g., Super-Admin operations). Every such route requires audit logging by design. |
| **ADLs** | Activities of Daily Living — bathing, dressing, eating, mobility, toileting. Standard home-care vocabulary used in care plans and visit documentation. |
| **Persona** | A role-based user archetype the product designs for, distinct from the literal `role` enum (the implementation). The product surface targets five personas: Caregiver, Family Member, Care Manager, Client, and Agency Admin — these are tenant-scoped. v2 design adds a sixth, Super-Admin, the platform-operator role that bypasses tenant Row-Level Security (see [`RLS-bypass surface`](#rls-bypass-surface) and [ADR-002](adr/002-postgresql-rls-multi-tenancy.md)); Super-Admin is forward-looking and has no v1 equivalent. |

## Process terms

| Term | Definition |
|------|-----------|
| **Pipeline command** | A slash command (`/define`, `/design`, `/implement`, `/review`, `/summarize`) that drives one stage of the engineering pipeline. See [CONTRIBUTING.md](../CONTRIBUTING.md). |
| **`make check`** | The pre-PR quality gate (lint + typecheck + test + build + script self-tests). CI runs the same checks; both must pass before merge. |
