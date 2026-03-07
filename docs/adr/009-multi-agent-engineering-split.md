# ADR-009: Multi-Agent Engineering Split

**Status:** Accepted
**Date:** 2026-03-07
**Related:** ADR-006 (Claude API)

## Context

A single AI model acting as both builder and validator creates correlated failure modes — shared blind spots, single-model groupthink, and no independent verification. The model that builds the code should not be the same model that validates it.

## Decision

Split engineering agent roles across two LLM backends: **Claude Code** (builder/executor) and **Google Gemini** (validator/risk manager).

### Guiding Principles

1. **Builders need tooling.** Claude Code has integrated file I/O, bash execution, git operations, and structured editing. Roles that touch code, infrastructure, or runtime belong on Claude Code.
2. **Validators should be independent.** Audit, review, and verification roles gain the most from running on a different model.
3. **Keep the boundary clean.** Concentrate building on Claude Code and auditing on Gemini. This simplifies coordination and makes handoff points explicit.
4. **Rationale must be technical, not marketing.** Assignments are based on demonstrated capability and architectural fit.

### Claude Code — Builder / Executor (7 roles)

| # | Role | Rationale |
|:--|:-----|:----------|
| 10 | **Engineering Manager** | Maintains consistent technical direction, rule adherence, and process enforcement. |
| 2 | **Software Engineer** | Primary code author. Integrated tooling (file editing, bash, git, multi-file operations). |
| 3 | **System Architect** | Architecture decisions grounded in intimate knowledge of the actual codebase. |
| 4 | **Data Engineer** | Implementation-heavy: writing migrations, building pipelines, optimizing queries. |
| 5 | **AI/ML Engineer** | Claude API integration — knows its own SDK and API best. |
| 1 | **UX Designer** | Translates designs into React/HTML/CSS. Requires generating and editing frontend code. |
| 8 | **SRE** | Operational: running commands, reading logs, restarting services, editing configs. |

### Google Gemini — Validator / Risk Manager (4 roles)

| # | Role | Rationale |
|:--|:-----|:----------|
| 6 | **Security Engineer** | Cross-model validation catches blind spots the builder's model would share. |
| 7 | **QA Engineer** | Independent verification and validation (IV&V) — different model maximizes edge case coverage. |
| 11 | **PM (Product Manager)** | Separates "what to build" from "how to build it" across model boundaries. |
| 9 | **Tech Writer** | Independent reader of builder output — flags unclear code/architecture rather than filling gaps with shared assumptions. |

### Build-then-Validate Flow

```
Claude Code builds --> Gemini validates --> Claude Code addresses feedback
```

1. **PM (Gemini)** writes requirements and acceptance criteria.
2. **EM (Claude Code)** plans the work, assigns tasks, oversees execution.
3. **Software Engineer, Architect, Data Eng, AI/ML Eng, UX Designer (all Claude Code)** implement the feature.
4. **QA Engineer (Gemini)** tests the implementation against requirements.
5. **Security Engineer (Gemini)** audits the code for vulnerabilities.
6. **SRE (Claude Code)** deploys and monitors.
7. **Tech Writer (Gemini)** documents the feature.

### Coordination Protocol

- **Structured artifacts** — PRDs, test reports, security findings, and review comments in a defined schema.
- **File-based exchange** — Both models read/write to the shared repository. The repo is the source of truth.
- **Explicit acceptance criteria** — The PM (Gemini) defines "done." The QA Engineer (Gemini) verifies "done." The EM (Claude Code) orchestrates the path between them.

## Consequences

### Positive
- Independent validation catches blind spots a single model would miss
- Security and QA audits are genuinely independent
- Clear separation of concerns between building and validating
- File-based coordination keeps the repo as single source of truth

### Negative
- Two AI systems to configure and maintain
- Cross-model handoffs add coordination overhead
- Requires structured artifact schemas both models understand

### Risks
- Coordination friction if artifact schemas diverge — mitigate with shared schema definitions in `docs/`
- Model capability gaps in assigned roles — mitigate by reassigning roles based on observed performance
