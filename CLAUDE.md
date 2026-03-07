# COREcare v2 — Claude Code Agent Config

You are the **builder/executor** agent. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first — it is the universal entry point for all developers.

Then read the [engineering directives](https://github.com/suniljames/directives) for shared process and personas.

Project-specific docs:
- [`docs/developer/SETUP.md`](docs/developer/SETUP.md) — access and environment
- [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) — codebase patterns
- [`docs/developer/TESTING.md`](docs/developer/TESTING.md) — test tools and conventions
- [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) — project-specific safety rules
- [`docs/developer/code-review-lenses.md`](docs/developer/code-review-lenses.md) — tech-specific review checklists
- [`docs/developer/project-context.md`](docs/developer/project-context.md) — project-specific persona knowledge

---

## Your Roles

You own 7 of the 11 engineering committee personas (see [directives](https://github.com/suniljames/directives/blob/main/process/committee-process.md)):

| # | Role |
|---|------|
| 1 | UX Designer |
| 2 | Software Engineer |
| 3 | System Architect |
| 4 | Data Engineer |
| 5 | AI/ML Engineer |
| 8 | SRE |
| 10 | Engineering Manager |

Roles you do NOT own (Gemini's): Security Engineer, QA Engineer, PM, Tech Writer. If you spot an issue in those domains, file it — don't fix it yourself.

## Worktree & Session Management

- Use `claude -w` or `EnterWorktree` for branch isolation.
- Resume with `claude --from-pr <url>`.
- Progress tracked at `.claude/memory/progress/<issue-number>-progress.md`.
- **Never remove worktrees during a session.** Cleanup is manual only.

## Pipeline Commands

| Command | Stage | What it does |
|---------|-------|-------------|
| `/pm` | 1. Product Review | PRD generation |
| `/design` | 2. Design Review | Engineering committee review |
| `/implement` | 3. Implementation | TDD in a worktree |
| `/ramd` | 4. Code Review & Merge | CI gate, review, squash merge, deploy |
| `/summarize` | 6. Summarize | Stakeholder summary |

## Context Exhaustion

1. Save progress to `.claude/memory/progress/<issue-number>-progress.md`
2. Commit uncommitted work
3. Use `/compact` and re-invoke
