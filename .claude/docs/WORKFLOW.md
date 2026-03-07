# Issue Implementation Workflow

Fully autonomous lifecycle. No human checkpoints.

## Label Lifecycle

```
/pm       -> adds `pm-reviewed`
/design   -> checks `pm-reviewed`, adds `design-complete`
/implement -> checks `design-complete`, adds `implementing`
/ramd     -> checks CI + labels, after merge: adds `merged`, removes `implementing`
/summarize -> adds `summarized` (optional, after deploy)
```

Each command warns but does not block if the prior stage's label is missing.

> **WORKTREE RULE:** Never remove worktrees during a session. Cleanup is manual only.

## Session Startup

1. **Determine the issue** — from arguments, conversation, or create a new one
2. **Create worktree** — `claude -w` or `EnterWorktree`
3. **Verify main checkout** is on `main`

## 1. Setup

- Create isolated worktree
- Verify Docker services running: `docker compose ps`

## 2. Scaffold Tests (RED)

Before writing any feature code:

1. Read the **Test Specification** from the GitHub issue
2. If no Test Specification: write 2-3 criteria from the issue description
3. Create test files at appropriate layers:
   - **API service tests:** `api/app/tests/test_{domain}.py` (pytest + httpx)
   - **API integration tests:** `api/app/tests/test_{domain}_api.py` (FastAPI TestClient)
   - **Web component tests:** `web/src/**/__tests__/*.test.ts` (vitest + testing-library)
   - **E2E tests:** `web/e2e/*.spec.ts` (Playwright)
4. Write failing tests
5. Commit: `test(#<issue>): scaffold failing tests`
6. Run tests to confirm they fail correctly

> **Service tests first.** Start with API service-layer tests — fastest, no UI dependency.

## 3. Implement (GREEN -> REFACTOR)

- Write minimum code to pass tests
- Run `make check` after each meaningful change
- Refactor once green
- **API:** routers -> services -> models. Pydantic schemas for I/O.
- **Web:** Server Components default. Client Components for interactivity. shadcn/ui.
- Commit early and often

## 4. Verify (pre-PR)

- All tests GREEN
- `make check` passes (lint + typecheck + test + build)
- **Only proceed if `make check` passes at 100%**

## 5. PR & Code Review (via `/ramd`)

`/ramd` handles:
1. Creates PR (push + `gh pr create`)
2. Waits for CI
3. Runs autonomous eng-committee code review (up to 3 rounds)
4. Squash merges

## 6. Deploy & Close

- `docker compose up --build -d`
- Verify `curl http://localhost:8000/healthz`
- Close issue with summary comment
- **Do NOT clean up the worktree**

## Multi-Phase Issues

Complete each phase as a separate PR. Use `/compact` between phases.

## Progress Tracking

Progress files at `.claude/memory/progress/<issue-number>-progress.md`.
Written at PR creation and completion.

## Context Exhaustion

1. Save progress to file
2. Commit uncommitted work
3. Use `/compact` and re-invoke
