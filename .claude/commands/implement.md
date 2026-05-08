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
- **`--force-on-closed`** — see "Gate: issue state" below

## Gate: issue state

> Mirrors the gate in `define.md` / `design.md` / `implement.md` / `review.md`.
> When editing this gate, update all four files in lockstep.

This gate **aborts** the skill if the GitHub issue is CLOSED, unless the
operator passes `--force-on-closed`. It runs **after** argument parsing and
**before** any side-effecting step — specifically before adding the
`implementing` label, before `EnterWorktree`, and before the branch base cut.

### Parse `$ARGUMENTS`

```bash
ARGS=( $ARGUMENTS )
FORCE_ON_CLOSED=false
ISSUE_NUMBER=""
for arg in "${ARGS[@]}"; do
  case "$arg" in
    --force-on-closed) FORCE_ON_CLOSED=true ;;
    *)
      stripped="${arg##\#}"
      if [[ "$stripped" =~ ^[0-9]+$ ]]; then
        ISSUE_NUMBER="$stripped"
      fi
      ;;
  esac
done
```

If `ISSUE_NUMBER` is empty after parsing, fall back to the context-inferred
issue (per "Parse arguments" above).

### State + closed-by lookup (single call)

```bash
ISSUE_META=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" \
  --json state,title,closedByPullRequestsReferences)
ISSUE_STATE=$(echo "$ISSUE_META" | jq -r '.state')
ISSUE_TITLE=$(echo "$ISSUE_META" | jq -r '.title')
CLOSED_BY_PR=$(echo "$ISSUE_META" | jq -r '.closedByPullRequestsReferences[0].number // empty')
CLOSED_BY_TITLE=$(echo "$ISSUE_META" | jq -r '.closedByPullRequestsReferences[0].title // empty')
```

### Gate behavior

- If `ISSUE_STATE == "CLOSED"` and `FORCE_ON_CLOSED == false`:
  - Print the canonical abort message (below).
  - Perform **no further actions** — do not add the `implementing` label, do
    not create a worktree, do not cut a branch.
  - Stop the skill (return non-zero).
- Else: proceed to the next section.

### Canonical abort message

```
Issue #<n> "<title>" is CLOSED.

Pipeline commands abort on closed issues by default — this prevents
post-hoc design or implementation runs (the failure mode that
surfaced this gate; see issue #213).

  Closed by: PR #<pr> "<pr-title>"        ← shown when discoverable

To proceed:
  • Reopen the issue:
        gh issue reopen <n> --repo <repo>
  • Or override on this run:
        /<command> <n> --force-on-closed
```

The `Closed by:` line is shown only when `CLOSED_BY_PR` is non-empty.

## Lifecycle check: design-complete

Check if the `design-complete` label exists. If missing, log warning and proceed (autonomous mode).

## Add implementing label

```bash
gh label create "implementing" --color "fbca04" --description "Implementation in progress" --repo "$REPO" 2>&1 | grep -v "already exists" || true
gh issue edit <number> --repo "$REPO" --add-label "implementing"
```

## Branch base — cut from freshly-fetched origin/main

Before creating the feature branch (whether via `EnterWorktree` or manually
inside an existing worktree), ensure the cut is from a freshly-fetched
`origin/main`, not stale local `main`.

```bash
# Cut from origin/main, not local main — see issue #176.
git fetch origin main
BASE_SHA=$(git rev-parse origin/main)
if [[ -z "$BASE_SHA" || ! "$BASE_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "ERROR: could not resolve origin/main to a SHA. Aborting." >&2
  exit 1
fi
echo "Cutting from origin/main @ ${BASE_SHA:0:8}"
LOCAL_BEHIND=$(git rev-list --count "main..origin/main" 2>/dev/null || echo 0)
if [[ "$LOCAL_BEHIND" -gt 0 ]]; then
  echo "Local main was $LOCAL_BEHIND commits behind origin/main; using origin/main as the base."
fi
git checkout -b "<feature-branch-name>" "$BASE_SHA"
```

Rules:
- Do **not** silence stderr from `git fetch`. Failure must be loud and abort.
- Do **not** fall back to local `main` under any condition.
- Do **not** auto-delete an existing local branch — fail clearly if the target name already exists.

## Worktree isolation

Use `EnterWorktree` to create an isolated worktree under `.claude/worktrees/`.
After the worktree exists, apply the **Branch base** block above before any
other branching/checkout work.

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

## Proceed to /review

Autonomous mode: proceed directly to `/review`. No human review checkpoint.
