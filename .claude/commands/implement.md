Read the GitHub issue and implement it using test-first development in a worktree.

## Repo Detection

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
```

Validate: if `$REPO` is empty or does not contain `/`, abort with:
> "Could not detect repository from git remote. Run this from inside the COREcare-v2 repo."

Use `--repo "$REPO"` on every `gh` command.

## Parse arguments

Parse `$ARGUMENTS` for:
- **Issue number** — a `#`-prefixed or bare number

## Lifecycle check: design-complete

Check if the `design-complete` label exists. If missing, log warning and proceed (autonomous mode).

## Add implementing label

```bash
gh label create "implementing" --color "fbca04" --description "Implementation in progress" --repo "$REPO" 2>&1 | grep -v "already exists" || true
gh issue edit <number> --repo "$REPO" --add-label "implementing"
```

## Worktree isolation

Use `EnterWorktree` to create an isolated worktree under `.claude/worktrees/`.

## Test-first scaffolding (RED)

Before writing feature code:

1. Read the **Test Specification** from the GitHub issue
2. If no Test Specification (ad-hoc issue):
   - Write 2-3 acceptance criteria from the issue description
3. Create test files at appropriate layers:
   - **API service tests:** `api/app/tests/test_{domain}.py` using pytest + httpx
   - **API integration tests:** `api/app/tests/test_{domain}_api.py` testing endpoints
   - **Web unit tests:** `web/src/**/__tests__/*.test.ts` using vitest
   - **E2E tests:** `web/e2e/*.spec.ts` using Playwright
4. Write failing tests
5. Commit: `test(#<issue>): scaffold failing tests from test specification`
6. Run tests to confirm they fail for the right reason

## Implement the feature (GREEN -> REFACTOR)

- Write minimum code to make failing tests pass
- Run `make check` after meaningful changes
- Once all tests pass, refactor as needed
- **API patterns:** Routers -> Services -> Models. No business logic in routers.
- **Web patterns:** Server Components default. Client Components for interactivity. shadcn/ui.
- **Shared component reuse:** Search existing components before creating new ones.
- Commit early and often

## Visual Alignment Verification (UI changes only)

If SVG mockups exist in `docs/mockups/<issue-number>/`:
1. UX Designer persona compares implementation against mockups
2. Post Visual Alignment Report as PR comment
3. Fix misalignments before proceeding

## Pre-PR gate

```bash
make check
```

All linters, type checks, tests, and build must pass.

## Write progress file

Create `.claude/memory/progress/<issue-number>-progress.md` with status.

## Proceed to /ramd

Autonomous mode: proceed directly to `/ramd`. No human review checkpoint.
