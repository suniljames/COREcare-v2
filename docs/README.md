# COREcare v2 — Documentation

You're inside `docs/`. Pick a lane.

## Start by role

| You are a... | Start here | Then read |
|---|---|---|
| **Backend engineer** | [`developer/README.md`](developer/README.md) | [`developer/ARCHITECTURE.md`](developer/ARCHITECTURE.md) → [`developer/TESTING.md`](developer/TESTING.md) → [`developer/SAFETY.md`](developer/SAFETY.md) |
| **Frontend engineer** | [`design-system/README.md`](design-system/README.md) | [`design-system/COMPONENTS.md`](design-system/COMPONENTS.md) → [`design-system/ACCESSIBILITY.md`](design-system/ACCESSIBILITY.md) → [`developer/TESTING.md`](developer/TESTING.md) |
| **Code reviewer** | [`developer/code-review-lenses.md`](developer/code-review-lenses.md) | The persona for your role + [`adr/`](adr/) for past decisions |
| **On-call / operator** | [`operations/README.md`](operations/README.md) | The runbook matching the alert |
| **Porting v1 behavior to v2** | [`migration/README.md`](migration/README.md) | The locked conventions inside |
| **Looking up a past decision** | [`adr/README.md`](adr/README.md) | The ADR(s) covering the area you're touching |
| **Looking up a domain term** | [`GLOSSARY.md`](GLOSSARY.md) | The cross-references in each definition |

## Directory map

| Directory | Purpose | When to read |
|---|---|---|
| [`adr/`](adr/) | 11 numbered Architecture Decision Records — the *why* behind tech choices | Before proposing a major architectural change, or when you want to know why a decision was made |
| [`developer/`](developer/) | Core engineering reference — architecture, testing, safety, code review, project context | On every contribution |
| [`design-system/`](design-system/) | shadcn/ui tokens, components, accessibility, brand, content guide | When building anything frontend |
| [`migration/`](migration/) | v1 → v2 reference docset (pages, journeys, integrations, glossary, locked conventions, CI-validated) | Only if porting v1 behavior to v2 |
| [`legacy/`](legacy/) | v1 UI screenshot catalog (Git-LFS, locked refresh procedure) | Only if studying v1 UI for reference |
| [`operations/`](operations/) | Operator runbooks (recovery, on-call procedures) | Only if you're operating the running system |
| [`mockups/`](mockups/) | Design mockups (visual reference, may lag implementation) | When you need a visual target for a feature; the running app is the source of truth |
| [`strategy/`](strategy/) | Business strategy (market analysis, pricing, competitive landscape) | Only if you're a PM or stakeholder; engineers can ignore |
| [`GLOSSARY.md`](GLOSSARY.md) | Canonical domain vocabulary | Whenever a term is new — persona, tenant, RLS, PHI, ADLs, etc. |

## Common questions

**What's a "persona" in this product?**
A role-based user archetype the product designs for — Caregiver, Family Member, Care Manager, Agency Admin, Super-Admin. It's the *experience* that role gets, distinct from the literal `role` enum. Full table in [`GLOSSARY.md`](GLOSSARY.md).

**How is multi-tenancy enforced?**
PostgreSQL Row-Level Security (RLS) at the database layer. Every tenant-scoped table has a policy keyed on `app.current_tenant_id`, set per-request from the authenticated user's `agency_id`. See [ADR-002](adr/002-postgresql-rls-multi-tenancy.md) for the decision and [`developer/ARCHITECTURE.md`](developer/ARCHITECTURE.md) for the implementation pattern.

**How do I add a database migration?**
*Currently blocked by [#240](https://github.com/suniljames/COREcare-v2/issues/240)* — schema-init is broken (no migration creates the initial tables). Once that's resolved, the workflow will be: create a new revision under `api/alembic/versions/`, run `make api-migrate` against a fresh DB, add a test, ship. Until then, schema lives in `SQLModel.metadata.create_all` in test fixtures.

## What's *not* here

- Production secrets, API keys, customer data — never in this repo.
- AI agent configs ([`CLAUDE.md`](../CLAUDE.md), [`GEMINI.md`](../GEMINI.md)) — at the repo root, only relevant if you're using those tools.
- Setup mechanics — start at the root [`README.md`](../README.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md) for `make setup` and the dev workflow.
