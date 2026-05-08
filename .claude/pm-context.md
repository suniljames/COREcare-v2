# PM Persona Context — COREcare v2

> **Canonical domain vocabulary lives in [`docs/GLOSSARY.md`](../docs/GLOSSARY.md).** The vocabulary table below is retained here as agent-facing context (the rest of this file — stakeholders, workflows, compliance hard rules, decision heuristics — is the AI-agent extension on top of the canonical glossary). If a definition disagrees, `docs/GLOSSARY.md` is authoritative.

## Domain

Multi-tenant SaaS for home health agencies. COREcare connects caregivers, family members, and agency administrators around a shared patient/client record. A platform-level super-admin manages all tenant agencies.

## Domain Vocabulary

| Term | Definition |
|------|-----------|
| **Agency** | A home care business that employs caregivers and serves clients. Each agency is a tenant. |
| **Care Plan** | A structured document defining a client's care needs, goals, interventions, and schedule. |
| **Care Manager** | Supervising nurse or coordinator who creates care plans and oversees caregiver assignments. |
| **Caregiver** | Field worker (RN, CNA, HHA, therapist) who provides direct care in client homes. |
| **Client** | The person receiving home care services (often elderly or disabled). |
| **Family Member** | A client's relative or authorized representative with limited platform visibility. |
| **Visit** | A scheduled caregiver-client interaction with clock-in/out, tasks, and documentation. |
| **Shift** | A time block during which a caregiver is assigned to a client. |
| **Super-Admin** | Platform operator who can see all agencies (bypasses RLS). |
| **Tenant** | An agency and all its associated data, isolated by PostgreSQL Row-Level Security. |
| **ADLs** | Activities of Daily Living — bathing, dressing, eating, mobility, toileting. |
| **PHI** | Protected Health Information — any individually identifiable health data. |

## Stakeholders

| Persona | Typical User | Key Needs |
|---------|-------------|-----------|
| Super-Admin | Platform owner | Agency management, impersonation, platform metrics |
| Agency Admin | Agency manager | Scheduling, compliance, oversight, billing |
| Care Manager | Supervising nurse | Team oversight, care plan management |
| Caregiver | Nurse, CNA, HHA | Efficient documentation, clear assignments, minimal paperwork |
| Family Member | Spouse, adult child | Visibility, peace of mind, communication |

*(Super-Admin is v2 forward-looking; v1 has no Super-Admin role — `is_superuser`-gated views fold into Agency Admin per [#236](https://github.com/suniljames/COREcare-v2/issues/236).)*

## Key Workflows

| Workflow | Description |
|----------|-------------|
| Shift management | Scheduling, assignment, clock-in/out, handoff notes |
| Visit documentation | Vitals, medications, ADLs, incident reports |
| Charting | Ongoing patient records visible to the care team |
| Family portal | Read-only (or limited-write) view for family members |
| Notifications | Shift reminders, schedule changes, care plan updates |
| Billing & Payroll | Period calculations, invoicing, QuickBooks integration |
| Credentialing | License/cert tracking, expiration alerts |
| AI Assistant | Conversational care coordination, smart scheduling |

## Privacy / Data Model

- **Multi-tenant isolation via PostgreSQL RLS** — each agency sees only its own data.
- **Role-based visibility** — caregivers see only their assigned clients; families see only their linked client.
- **Super-Admin bypass** — platform operators can see all tenants for support and onboarding.
- **Minimum Necessary Rule** — only expose the PHI needed for a given role.
- **Audit logging** — who accessed what, when, and why.

## Compliance

- **HIPAA** — All client health data is PHI. Encryption at rest and in transit. Audit logging for access. BAA required with third-party services.
- **State home care regulations** — vary by state; care plan structure must be flexible.

**Hard rules:**
- Never expose cross-tenant data in API responses
- Never include PHI in error messages, logs, or analytics
- Never store PHI in browser localStorage or unencrypted cookies
- Never include diagnosis, medications, or detailed health data in notifications (email, SMS, push)
- All data-access endpoints must have tenant isolation tests
- AI features must redact PHI before sending to external APIs

## Decision Heuristics

- Default to the **caregiver's mobile experience** — they are the highest-volume, lowest-patience user
- When in doubt about data visibility, **restrict access** and let admins widen it
- Prefer **structured data** (dropdowns, checklists) over free-text for care documentation — aids reporting and AI analysis
- **Offline-capable** where possible — caregivers work in homes with unreliable connectivity
- Keep agency onboarding **self-service** — minimize super-admin involvement
- Features should work for a **single-caregiver agency** and a **200-caregiver agency** alike

## Anti-Patterns

- No direct access to another agency's data, even for "reporting"
- No bulk export of PHI without audit trail
- No real-time location tracking of caregivers
- No social features or inter-agency communication
- No storing care credentials (medical record numbers, SSNs) in the platform
- No gamification of care quality metrics

## Product Phase

Early build (v0.x) — ground-up rebuild. Core entities (agencies, users, clients, care plans, visits) are being established. Keep scope tight — build the foundation before adding AI-powered features.

## Communication Channels

- **Primary:** Web application (desktop for admins/managers, mobile-responsive for caregivers)
- **Notifications:** In-app + email (future: SMS/push)
- **AI:** Claude API for care plan assistance, documentation help, and insights (future phases)
- **No SMS yet** — planned for caregiver alerts and family updates
