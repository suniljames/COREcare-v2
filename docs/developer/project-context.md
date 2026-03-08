# COREcare Project Context

Project-specific persona knowledge and engineering compromises. This extends the generic personas and cross-cutting traits in [`suniljames/directives`](https://github.com/suniljames/directives).

## Tech Stack Compromises

| Focus Area | Scale Experience Logic | COREcare Reality | Compromise |
|:---|:---|:---|:---|
| **Testing** | 100% coverage, integration suites | Local Docker Compose, fast iteration | Critical-path tests + structured logging + `make check` gate |
| **Data** | Microservices, sharding | Single PostgreSQL 16 with RLS | Monolithic DB with strict schema discipline via Alembic |
| **Infrastructure** | Custom K8s clusters | Local Mac Mini, Docker Compose | Managed simplicity until scale forces migration |
| **Process** | Formal sprint planning | Autonomous AI-driven workflow | GitHub Issues + autonomous pipeline |

## Persona: Project-Specific Knowledge

### UX Designer

| Expertise | COREcare Application |
|-----------|---------------------|
| Design systems | shadcn/ui + Tailwind CSS token system, `docs/design-system/` compliance |
| Accessibility | WCAG 2.1 AA across all viewports, axe-core test coverage |
| Responsive design | Mobile (<=480px), Tablet (481-1024px), Desktop (>1024px) breakpoints |
| Healthcare UX | Caregiver shift views, family portal, medication tracking, visit logs |
| Component reuse | Shared component library across admin, caregiver, and family portals |
| Multi-tenant UI | Agency branding, tenant-scoped navigation, super-admin views |

### Software Engineer

| Expertise | COREcare Application |
|-----------|---------------------|
| API design | FastAPI service layer pattern (routers -> services -> models) |
| Frontend patterns | Next.js 15 App Router, Server Components by default, Client for interactivity |
| Component reuse | shadcn/ui shared components across admin, caregiver, and family portals |
| Type safety | Pydantic v2 schemas (API), TypeScript strict mode (web) |
| Code quality | `make check` gate: linters, type checking, tests, build |
| Auth integration | Clerk JWT validation in FastAPI dependencies |

### System Architect

| Expertise | COREcare Application |
|-----------|---------------------|
| Multi-tenancy | PostgreSQL RLS policies, tenant context propagation via Clerk JWT |
| Service layer | FastAPI routers -> services -> models pattern, no business logic in routers |
| App Router | Next.js 15 route groups, layouts, loading/error boundaries |
| Data isolation | RLS enforcement on every query, super-admin bypass for cross-tenant views |
| Deployment | Docker Compose on local Mac Mini, single-node simplicity |
| Event patterns | Domain events for audit logging, notification triggers |

### Data Engineer

| Expertise | COREcare Application |
|-----------|---------------------|
| Schema design | SQLModel models, PostgreSQL 16, proper relationships and constraints |
| Migrations | Alembic migrations: reversible, separate data from schema, tested rollbacks |
| Multi-tenancy | RLS policies on every table, `agency_id` tenant isolation |
| Query performance | Async PostgreSQL sessions, eager loading, index optimization |
| Audit trails | Temporal tracking for care plans, medication changes, visit logs |
| Data integrity | Foreign keys, check constraints, unique constraints for business rules |

### AI/ML Engineer

| Expertise | COREcare Application |
|-----------|---------------------|
| Claude API | Anthropic SDK integration, structured outputs for care insights |
| Prompt safety | PHI redaction before LLM calls, no patient data in prompts without necessity |
| Agent patterns | AI agent foundation for care coordination assistance |
| RAG | Document retrieval for care plans, policy lookup, compliance checking |
| Cost management | Token tracking, model selection (Haiku vs Sonnet vs Opus), caching |
| Audit trail | Logging all AI interactions for HIPAA compliance and quality review |

### Security Engineer

| Expertise | COREcare Application |
|-----------|---------------------|
| HIPAA | PHI handling, minimum necessary principle, BAA tracking, audit logs |
| Auth | Clerk JWT validation, role-based access control (super-admin, admin, manager, caregiver, family) |
| Multi-tenancy | RLS policy verification, cross-tenant isolation testing |
| Input validation | Pydantic schemas for API input, sanitization for user-facing content |
| Logging | PHI exclusion from logs, structured audit logging for compliance |
| Secrets | Environment variable management, no secrets in code or Docker images |

### QA Engineer

| Expertise | COREcare Application |
|-----------|---------------------|
| Test layers | pytest (service/endpoint), vitest (components), Playwright (E2E) per [test-budget.md](https://github.com/suniljames/directives/blob/main/teams/engineering/process/test-budget.md) |
| Test format | Given/When/Then specs for all test layers |
| Quality gates | `make check` must pass: linters + tests + typecheck + build |
| CI | GitHub Actions against PostgreSQL 16 |
| Multi-tenant testing | Tenant isolation verification in service tests for every data-access endpoint |
| Test markers | `@smoke`, `@security` for Playwright; unmarked for standard tests |

### SRE

| Expertise | COREcare Application |
|-----------|---------------------|
| Deployment | Docker Compose on local Mac Mini, `docker compose up --build -d` |
| Health checks | `/healthz` endpoint, container health checks, service dependencies |
| Logging | structlog for structured JSON logging, context propagation |
| Networking | Tailscale for remote access from other devices |
| Resource management | PostgreSQL connection pooling, Redis connection management |
| Monitoring | Health check verification, container resource usage tracking |

### Writer

| Expertise | COREcare Application |
|-----------|---------------------|
| UX writing | User-facing copy across admin, caregiver, and family portals |
| Error messages | Helpful, actionable errors that don't expose PHI or internal state |
| Notifications | Push notification copy, email templates, in-app messages |
| API messages | Consistent API error response messages |
| Documentation | Developer docs, ADRs, design system documentation |
| Accessibility | Alt text, ARIA labels, meaningful link text, screen reader support |

### Engineering Manager

| Expertise | COREcare Application |
|-----------|---------------------|
| Decision synthesis | Resolving committee disagreements into actionable decisions |
| Technical strategy | Balancing HIPAA compliance, shipping speed, and maintainability |
| Architecture review | Evaluating multi-tenant RLS, service layer, and deployment patterns |
| Priority calls | When committee members disagree, determining which concern wins |
| Tech debt tracking | Identifying shortcuts that need to be repaid and when |
| Operational health | Ensuring shipped features are operable, not just functional |

### PM

| Expertise | COREcare Application |
|-----------|---------------------|
| Personas | Caregiver, family member, care manager, agency admin, super-admin workflows |
| HIPAA | Privacy-by-default product decisions, minimum necessary data exposure |
| Multi-tenancy | Agency isolation in product UX, super-admin cross-agency views |
| Care workflows | Shift handoffs, medication tracking, visit logging, care plan management |
| Compliance | Audit trails as product features, not afterthoughts |
| Communication | Family messaging, notifications, care team coordination |
