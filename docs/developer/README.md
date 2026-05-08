# Engineering — `docs/developer/`

Core reference for anyone writing code in this repo. Read in the order below on day 1; come back to specific files as the work demands.

## Read first (in order)

| Doc | Use it for |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | How the codebase is laid out — service-layer pattern, RLS enforcement, Server vs Client components, the email outbound boundary, the AI orchestration approach. Start here on day 1. |
| [`SAFETY.md`](SAFETY.md) | Project-specific hard rules: PHI handling, audit logging, multi-tenant data isolation, what *never* goes in logs / errors / analytics. Read before touching anything that handles real data. |
| [`TESTING.md`](TESTING.md) | Test stack (pytest, vitest, Playwright), TDD workflow, test-layer priority, multi-tenancy test pattern. Read before writing your first test. |

## Reference (read when relevant)

| Doc | Use it for |
|---|---|
| [`code-review-lenses.md`](code-review-lenses.md) | Per-role checklists used by `/review`. If you're reviewing a PR or want to self-review before requesting one, find your role's lens here. |
| [`project-context.md`](project-context.md) | Project-specific persona expertise tables (UX Designer, Software Engineer, System Architect, etc.) and tech-stack compromises. Useful when an AI agent or new reviewer needs project-flavored context. |

## Cross-references

- **Why was X decided?** → [`../adr/`](../adr/) — 11 numbered Architecture Decision Records.
- **What does `tenant` / `persona` / `RLS` mean?** → [`../GLOSSARY.md`](../GLOSSARY.md).
- **Frontend specifics (tokens, components, a11y)?** → [`../design-system/`](../design-system/).
- **v1 → v2 migration reference?** → [`../migration/`](../migration/).

## What's *not* here

- Setup commands → [`../../README.md`](../../README.md) and [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).
- Operational runbooks → [`../operations/`](../operations/).
- v1 reference-doc validation conventions → [`../migration/doc-validation-conventions.md`](../migration/doc-validation-conventions.md). (They governed v1 reference docs, not v2 tests, so they live next to what they govern.)
