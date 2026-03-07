# Pipeline & Workflow

Fully autonomous lifecycle. No human review gates. Each stage produces artifacts the next stage consumes.

## Stages

| Stage | Purpose | Produces | Label |
|-------|---------|----------|-------|
| **1. Product Review** | Evaluate the issue, write a PRD with acceptance criteria | PRD comment on the GitHub issue | `pm-reviewed` |
| **2. Design Review** | Engineering committee reviews feasibility, architecture, UX, security | Design decision + test specification comments | `design-complete` |
| **3. Implementation** | TDD: scaffold failing tests -> implement -> green -> refactor | Code in a feature branch, all tests passing | `implementing` |
| **4. Code Review & Merge** | CI gate -> autonomous eng-committee code review (up to 3 rounds) -> squash merge | Merged PR | `merged` |
| **5. Deploy & Verify** | Docker rebuild, health check, close issue | Running deployment | Issue closed |
| **6. Summarize** (optional) | Plain-language stakeholder summary | Summary comment | `summarized` |

## Label Lifecycle

```
Product Review  -> adds `pm-reviewed`
Design Review   -> checks `pm-reviewed`, adds `design-complete`
Implementation  -> checks `design-complete`, adds `implementing`
Code Review     -> checks CI + labels, after merge: adds `merged`, removes `implementing`
Summarize       -> adds `summarized` (optional, after deploy)
```

Each stage warns but does not block if the prior stage's label is missing.

## Who Does What

| Stage | Gemini (validator) | Claude Code (builder) |
|-------|-------------------|----------------------|
| 1. Product Review | Writes the PRD, adds `pm-reviewed` | — |
| 2. Design Review | Security + QA lenses, test specification | Architecture, UX, data, SRE lenses |
| 3. Implementation | — | TDD: scaffold tests -> implement -> green |
| 4. Code Review | Security + QA review, post findings | Addresses findings, merges |
| 5. Deploy & Verify | — | Docker rebuild, health check, close issue |
| 6. Summarize | Tech Writer summary | — |

## Cross-Agent Handoff Protocol

- **The repo is the source of truth.** All handoffs happen through files, PR comments, and issue comments — never through inter-agent messages.
- **Structured artifacts:** PRDs, test reports, security findings, and review comments follow defined formats (see [`TEAM.md`](TEAM.md) for test spec format).
- **Label-driven coordination:** Agents check GitHub issue labels to determine which pipeline stage is complete before proceeding.
- **PR labels:** All autonomously created PRs are labeled `ai:autonomous`.
- **Review findings:** Posted as PR comments with severity levels: `MUST-FIX`, `SHOULD-FIX`, `NIT`.

## Implementation Workflow (Stage 3)

### 1. Setup

- Create isolated branch or worktree
- Verify Docker services running: `docker compose ps`

### 2. Scaffold Tests (RED)

1. Read the **Test Specification** from the GitHub issue
2. If no Test Specification: write 2-3 criteria from the issue description
3. Create test files at appropriate layers (see [`TESTING.md`](TESTING.md))
4. Write failing tests
5. Commit: `test(#<issue>): scaffold failing tests`
6. Run tests to confirm they fail correctly

> **Service tests first.** Start with API service-layer tests — fastest, no UI dependency.

### 3. Implement (GREEN -> REFACTOR)

- Write minimum code to pass tests
- Run `make check` after each meaningful change
- Refactor once green
- Commit early and often

### 4. Verify (pre-PR)

- All tests GREEN
- `make check` passes (lint + typecheck + test + build)
- **Only proceed to code review if `make check` passes at 100%**

## Multi-Phase Issues

Complete each phase as a separate PR.
