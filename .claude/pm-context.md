# COREcare v2 Product & Domain Context

This file provides domain context for the PM persona used in `/pm`.

## Product

**COREcare v2** is a multi-tenant SaaS platform for home health agencies.
It connects caregivers, family members, and agency administrators around
a shared patient/client record. A platform-level super-admin manages all
tenant agencies.

## Domain: In-Home Medical Care

- **Caregivers** include registered nurses (RNs), certified nursing assistants
  (CNAs), home health aides (HHAs), and therapists. They perform shift-based
  visits, document vitals, administer medications, and chart patient progress.
- **Family members** need visibility into their loved one's care — who visited,
  what was done, and whether the care plan is being followed.
- **Agency administrators** manage caregiver assignments, schedules, compliance
  documentation, and agency operations.
- **Platform super-admin** manages all agencies, can impersonate users, and
  monitors platform-wide metrics.

### Key Workflows

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

## Compliance: HIPAA

COREcare handles **Protected Health Information (PHI)** and must comply with
HIPAA requirements:

- **Minimum Necessary Rule** — only expose the PHI needed for a given role
- **Access controls** — role-based permissions (super-admin > agency-admin > care-manager > caregiver > family)
- **Audit logging** — who accessed what, when, and why (event-sourced)
- **PHI in transit and at rest** — encrypted connections (HTTPS), encrypted database
- **Notification content** — never include diagnosis, medications, or detailed health data in emails, SMS, or push notifications
- **Error messages and logs** — never expose PHI in user-facing errors or application logs
- **BAA** — Business Associate Agreements with third-party services

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12) |
| Frontend | Next.js 15 App Router + shadcn/ui |
| Database | PostgreSQL 16 with RLS |
| Auth | Clerk |
| AI | Claude API |
| Deployment | Docker Compose (local) |
| CI | GitHub Actions |

## Multi-Tenancy

Each agency is an isolated tenant. PostgreSQL Row-Level Security ensures
data isolation at the database level. The super-admin bypasses RLS for
platform management.

## User Personas

| Persona | Typical User | Key Needs |
|---------|-------------|-----------|
| Super-Admin | Platform owner | Agency management, impersonation, platform metrics |
| Agency Admin | Agency manager | Scheduling, compliance, oversight, billing |
| Care Manager | Supervising nurse | Team oversight, care plan management |
| Caregiver | Nurse, CNA, HHA | Efficient documentation, clear assignments |
| Family Member | Spouse, adult child | Visibility, peace of mind, communication |
