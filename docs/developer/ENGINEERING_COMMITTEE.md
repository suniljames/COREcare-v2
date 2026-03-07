# Engineering Committee ("eng-committee")

Convene the engineering committee for critical review of issues requiring cross-functional analysis. Three core principles:

1. **Sequential, iterative review** — Members post in strict order. Each reads all prior comments.
2. **Overwrite-to-final-consensus** — After deliberation, members whose positions changed overwrite their comments.
3. **Shared component reuse** — Every design must seek reuse opportunities across templates, components, services, and utilities.

## Committee Members

1. **UX Designer** (15y): Accessibility (WCAG), cognitive load, visual design, mockups. Mobile-first. shadcn/ui + Tailwind design system.
2. **Senior Software Engineer** (15y): Clean code, API integrity, FastAPI + Next.js patterns. Champions shared component reuse.
3. **System Architect** (15y): Multi-tenancy (RLS), service layer, Next.js App Router patterns, event-driven design.
4. **Principal Data Engineer** (15y): SQLModel/Alembic schema evolution, async PostgreSQL, RLS policy correctness.
5. **Principal AI/ML Engineer** (15y): Claude API patterns, RAG, prompt safety, agent orchestration.
6. **Principal Security Engineer** (15y): HIPAA compliance, Clerk auth, multi-tenant isolation, threat modeling.
7. **Principal QA Engineer** (15y): Test automation (pytest/vitest/Playwright), Given/When/Then specs, quality gates.
8. **Senior SRE** (15y): Docker Compose reliability, structured logging (structlog), health checks, resource management.
9. **Principal Writer** (15y): Content design, error messages, user-facing copy, Documentation Impact Assessment.

## The Judge (Principal Engineer)

20-year veteran. Synthesizes committee feedback to resolve conflicts. Prioritizes business outcomes, operational sustainability, and tech debt mitigation.

## UX Mockup Generation (UI/UX Changes Only)

- **When:** User-facing UI changes. Skip for backend/API/infra.
- **Design Direction:** Purpose, tone, design system alignment, typography, motion, anti-patterns.
- **Format:** SVG in `docs/mockups/<issue-number>/`
- **Responsive viewports:** Mobile (<=480px), Tablet (481-1024px), Desktop (>1024px)
- **Multiple states:** Default, error, success, loading for each viewport where they differ.

## Test Specification Format

```markdown
## Test Specification

### API Service Layer (pytest)
- GIVEN <precondition>
  WHEN <service method call>
  THEN <expected result/side effect>

### API Endpoint Layer (httpx/TestClient)
- GIVEN <auth state>
  WHEN <HTTP method + path>
  THEN <status code, response body>

### Web Component (vitest + testing-library)
- GIVEN <component props/state>
  WHEN <user interaction>
  THEN <rendered output>

### Browser (Playwright E2E)
- GIVEN <user role, viewport, page state>
  WHEN <user interaction>
  THEN <visible feedback, navigation>
  MARKERS: @smoke | @security | (none)
```

## Code Review Lenses (for /ramd)

See `.claude/commands/references/code-review-lenses.md` for role definitions, severity levels, and skip conditions.
