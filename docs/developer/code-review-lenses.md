# Code Review Lenses

> Persona backgrounds and generic review lenses are in the [engineering directives](https://github.com/suniljames/directives/blob/main/teams/engineering/process/code-review-framework.md).
> Below are the **COREcare-specific** technology checklists for each role.

Each engineering committee member reviews the PR diff through a **code-review-specific**
lens during `/ramd` Phase B.

## Severity Levels

| Severity | Meaning | Blocks merge? |
|----------|---------|---------------|
| **MUST-FIX** | Correctness bug, security vulnerability, data loss risk, or broken contract | Yes |
| **SHOULD-FIX** | Code quality issue, missing edge case, poor naming, or maintainability concern | Yes (in current round) |
| **NIT** | Style preference, minor suggestion, optional improvement | No |

---

## 1. UX Designer

**Skip if:** No frontend files (tsx, css, components) in the diff.

**What to look for:**
- WCAG 2.1 AA compliance (contrast, alt text, ARIA, focus management)
- Semantic HTML, form UX, tab order, keyboard navigation
- Responsive behavior (mobile-first, touch targets >= 44x44px)
- Design system compliance: shadcn/ui theme tokens, Tailwind config, no hardcoded values
- Visual hierarchy, intentional layout choices, motion with `prefers-reduced-motion`

---

## 2. Senior Software Engineer

**What to look for:**
- Code quality: DRY, dead code, complexity
- Naming clarity, readability (functions < 30 lines)
- FastAPI patterns: Pydantic schemas, dependency injection, proper status codes
- Next.js patterns: Server vs Client Components, proper data fetching
- Edge cases: empty inputs, None handling, error states

---

## 3. System Architect

**What to look for:**
- Service layer separation (routers -> services -> models)
- Multi-tenancy: RLS enforcement, tenant context propagation
- Coupling and cohesion, circular dependencies
- Next.js App Router patterns: route groups, layouts, loading/error boundaries

---

## 4. Principal Data Engineer

**What to look for:**
- Alembic migration safety: reversible, separate data from schema migrations
- Query performance: N+1, missing indexes, eager loading
- SQLModel/SQLAlchemy patterns: relationships, async sessions, transaction boundaries
- RLS policy correctness: tenant isolation verified

---

## 5. Principal AI/ML Engineer

**Skip if:** No AI/ML code (no Claude API calls, no prompt construction).

**What to look for:**
- Claude API: retry logic, timeout handling, cost tracking
- Prompt injection risks, PHI in prompts
- Fallback behavior when API unavailable
- Token usage management

---

## 6. Principal Security Engineer

**What to look for:**
- Injection vectors (SQL via raw queries, XSS, template injection)
- Auth bypass: missing Clerk middleware, role checks
- PHI exposure in logs, errors, URLs, API responses
- HIPAA: minimum necessary, audit logging for PHI access
- CSRF, secret handling, input validation
- Multi-tenant data leakage

---

## 7. Principal QA Engineer

**What to look for:**
- Test coverage for changed/added code
- Edge cases, assertion quality, fixture adequacy
- Test isolation, mock boundaries
- Correct test layer per TEST_BUDGET.md (service > integration > E2E)

---

## 8. Senior SRE

**What to look for:**
- Error handling: graceful degradation for external services
- Structured logging with context (structlog)
- Docker health checks, container resource usage
- Connection handling: timeouts, pool awareness

---

## 9. Principal Writer

**What to look for:**
- User-facing copy: helpful errors, clear labels
- API response messages: clear, no PHI
- Code comments: explain *why*, not *what*
- Commit message conventions: `feat`, `fix`, `test`, `docs`
