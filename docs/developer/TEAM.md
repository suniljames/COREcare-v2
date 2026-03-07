# Team Structure & Engineering Committee

## Multi-Agent Architecture

Two AI agents work this repo with distinct, non-overlapping roles. The builder and validator are different models to maximize independent verification.

| Agent | Role | Owns |
|-------|------|------|
| **Claude Code** | Builder / executor | Engineering Manager, Software Engineer, System Architect, Data Engineer, AI/ML Engineer, UX Designer, SRE |
| **Google Gemini** | Validator / risk manager | Security Engineer, QA Engineer, PM, Tech Writer |

**Flow:** Gemini PM defines requirements -> Claude Code builds -> Gemini QA/Security validates -> Claude Code addresses feedback.

See [`docs/adr/009-multi-agent-engineering-split.md`](../adr/009-multi-agent-engineering-split.md) for full rationale.

## Engineering Committee

The committee consists of 11 members. Each has a detailed persona definition.

| # | Role | Persona | Agent |
|---|------|---------|-------|
| 1 | UX Designer (15y) | [`01-ux-designer.md`](../organization/engineering/personas/01-ux-designer.md) | Claude Code |
| 2 | Senior Software Engineer (15y) | [`02-software-engineer.md`](../organization/engineering/personas/02-software-engineer.md) | Claude Code |
| 3 | System Architect (15y) | [`03-system-architect.md`](../organization/engineering/personas/03-system-architect.md) | Claude Code |
| 4 | Principal Data Engineer (15y) | [`04-data-engineer.md`](../organization/engineering/personas/04-data-engineer.md) | Claude Code |
| 5 | Principal AI/ML Engineer (15y) | [`05-ai-ml-engineer.md`](../organization/engineering/personas/05-ai-ml-engineer.md) | Claude Code |
| 6 | Principal Security Engineer (15y) | [`06-security-engineer.md`](../organization/engineering/personas/06-security-engineer.md) | Gemini |
| 7 | Principal QA Engineer (15y) | [`07-qa-engineer.md`](../organization/engineering/personas/07-qa-engineer.md) | Gemini |
| 8 | Senior SRE (15y) | [`08-sre.md`](../organization/engineering/personas/08-sre.md) | Claude Code |
| 9 | Principal Writer (15y) | [`09-writer.md`](../organization/engineering/personas/09-writer.md) | Gemini |
| 10 | Engineering Manager (20y) | [`10-engineering-manager.md`](../organization/engineering/personas/10-engineering-manager.md) | Claude Code |
| 11 | PM (senior) | [`11-pm.md`](../organization/engineering/personas/11-pm.md) | Gemini |

Shared team culture and principles: [`cross-cutting-traits.md`](../organization/engineering/cross-cutting-traits.md)

## Committee Process

Three core principles:

1. **Sequential, iterative review** — Members post in strict order. Each reads all prior comments.
2. **Overwrite-to-final-consensus** — After deliberation, members whose positions changed overwrite their comments.
3. **Shared component reuse** — Every design must seek reuse opportunities across templates, components, services, and utilities.

## UX Mockup Generation (UI/UX Changes Only)

- **When:** User-facing UI changes. Skip for backend/API/infra.
- **Design Direction:** Purpose, tone, design system alignment, typography, motion, anti-patterns.
- **Format:** SVG in `docs/mockups/<issue-number>/`
- **Responsive viewports:** Mobile (<=480px), Tablet (481-1024px), Desktop (>1024px)
- **Multiple states:** Default, error, success, loading for each viewport where they differ.

## Test Specification Format

Used during design review to define what must be tested.

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

## Code Review Lenses

See [`code-review-lenses.md`](code-review-lenses.md) for role-specific review checklists and severity levels (`MUST-FIX`, `SHOULD-FIX`, `NIT`).
