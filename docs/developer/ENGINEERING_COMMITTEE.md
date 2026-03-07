# Engineering Committee ("eng-committee")

Convene the engineering committee for critical review of issues requiring cross-functional analysis. Three core principles:

1. **Sequential, iterative review** — Members post in strict order. Each reads all prior comments.
2. **Overwrite-to-final-consensus** — After deliberation, members whose positions changed overwrite their comments.
3. **Shared component reuse** — Every design must seek reuse opportunities across templates, components, services, and utilities.

## Committee Members

Full persona definitions with backgrounds, expertise, and review lenses are in
[`docs/organization/engineering/personas/`](../organization/engineering/personas/).
Shared team culture and principles are in
[`docs/organization/engineering/cross-cutting-traits.md`](../organization/engineering/cross-cutting-traits.md).

| # | Role | Persona File |
|---|------|-------------|
| 1 | UX Designer (15y) | [`01-ux-designer.md`](../organization/engineering/personas/01-ux-designer.md) |
| 2 | Senior Software Engineer (15y) | [`02-software-engineer.md`](../organization/engineering/personas/02-software-engineer.md) |
| 3 | System Architect (15y) | [`03-system-architect.md`](../organization/engineering/personas/03-system-architect.md) |
| 4 | Principal Data Engineer (15y) | [`04-data-engineer.md`](../organization/engineering/personas/04-data-engineer.md) |
| 5 | Principal AI/ML Engineer (15y) | [`05-ai-ml-engineer.md`](../organization/engineering/personas/05-ai-ml-engineer.md) |
| 6 | Principal Security Engineer (15y) | [`06-security-engineer.md`](../organization/engineering/personas/06-security-engineer.md) |
| 7 | Principal QA Engineer (15y) | [`07-qa-engineer.md`](../organization/engineering/personas/07-qa-engineer.md) |
| 8 | Senior SRE (15y) | [`08-sre.md`](../organization/engineering/personas/08-sre.md) |
| 9 | Principal Writer (15y) | [`09-writer.md`](../organization/engineering/personas/09-writer.md) |

## Engineering Manager

20-year veteran. Synthesizes committee feedback to resolve conflicts. Prioritizes business outcomes, operational sustainability, and tech debt mitigation.

Full persona: [`10-engineering-manager.md`](../organization/engineering/personas/10-engineering-manager.md)

## Product Manager

Senior PM with deep consumer healthcare experience. Defines *what* and *why*, not *how*.

Full persona: [`11-pm.md`](../organization/engineering/personas/11-pm.md)

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

See `docs/developer/code-review-lenses.md` for role definitions, severity levels, and skip conditions.
