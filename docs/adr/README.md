# Architecture Decision Records

Numbered, dated, and decision-focused records of the major technical choices that shape COREcare v2. Each ADR captures the context, the decision, the alternatives considered, and the consequences.

| # | Decision | Touches |
|---|---|---|
| [001](001-fastapi-nextjs-architecture.md) | FastAPI + Next.js Architecture | Backend / frontend split, API contract |
| [002](002-postgresql-rls-multi-tenancy.md) | PostgreSQL RLS for Multi-Tenancy | DB, auth, every tenant-scoped query |
| [003](003-clerk-authentication.md) | Clerk for Authentication | Auth flows, JWT validation, sessions |
| [004](004-sqlmodel-orm.md) | SQLModel for ORM | Models, schemas, migrations |
| [005](005-docker-compose-local-deployment.md) | Docker Compose Local Deployment | Local dev, the `make` targets |
| [006](006-claude-api-ai-features.md) | Claude API for AI Features | AI orchestration, prompt construction |
| [007](007-event-sourced-audit-logging.md) | Event-Sourced Audit Logging | Audit trail, RLS-bypass surfaces |
| [008](008-shadcn-ui-component-library.md) | shadcn/ui Component Library | Frontend component library |
| [009](009-multi-agent-engineering-split.md) | Multi-Agent Engineering Split | Builder vs validator roles, pipeline |
| [010](010-v1-ui-catalog-storage.md) | v1 UI Screenshot Catalog Storage | `docs/legacy/`, Git LFS |
| [011](011-email-outbound-boundary.md) | Email Outbound Boundary | Email transport, PHI rules in messages |
| [012](012-cloud-pilot-hosting.md) | Cloud Pilot Hosting (Render + Vercel + R2) | Pilot-env deploy target; partially supersedes ADR-005 |

## When to write a new ADR

Write an ADR when you're proposing a decision that will be **expensive to reverse** — a tech choice, a new architectural pattern, a major library swap. Don't write an ADR for tactical implementation choices that any future change can revisit cheaply.

Convention: numbered sequentially, kebab-case filename, ADR title as `# ADR-NNN: Decision Name`. Status field at the top (Proposed / Accepted / Superseded). Sections: Context, Decision, Alternatives, Consequences. Look at any existing ADR for the shape.
