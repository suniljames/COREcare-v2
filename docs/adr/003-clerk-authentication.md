# ADR-003: Clerk for Authentication

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-001 (Architecture), ADR-002 (RLS)

## Context

COREcare v2 needs robust authentication across web (Next.js) and API (FastAPI) with support for multiple agencies, role-based access, and eventual SSO. Building auth from scratch is a security risk and maintenance burden.

Options considered:
1. **Custom auth** (password hashing, JWT, session management) — full control, high maintenance
2. **Auth0** — mature, expensive at scale
3. **Clerk** — developer-friendly, excellent Next.js integration, reasonable pricing
4. **Supabase Auth** — good but tightly coupled to Supabase ecosystem

## Decision

Use **Clerk** for authentication.

- **Frontend:** Clerk React components for sign-in, sign-up, user management
- **Backend:** JWT validation middleware for FastAPI (verify Clerk-issued JWTs)
- **User sync:** Clerk webhooks create/update local user records in our database
- **Role storage:** Clerk public metadata stores the user's role; local DB is source of truth for permissions

## Consequences

### Positive
- Battle-tested auth with MFA, social login, magic links out of the box
- Excellent Next.js App Router integration (middleware, server components)
- Handles password hashing, session management, token rotation
- Reduces our security surface area significantly
- Pre-built UI components speed up development

### Negative
- External dependency — Clerk outage affects all authentication
- Webhook sync adds complexity (eventual consistency between Clerk and local DB)
- Cost scales with active users
- Less control over auth flow customization

### Risks
- Clerk service disruption — mitigate with cached JWTs and graceful degradation
- Webhook delivery failures — mitigate with idempotent handlers and reconciliation job
