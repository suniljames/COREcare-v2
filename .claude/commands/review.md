/review — Review gates. Approve. Merge. Deploy.

Create the PR (if needed), run quality gates, perform autonomous eng-committee
code review, merge via squash, and verify Docker deployment.

## Repo Detection

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
```

Use `--repo "$REPO"` on every `gh` command.

---

# Phase 0: PR Creation (when no PR exists)

## 0.1: Detect issue context

Find the linked issue from progress file, branch name, or commit messages.
Store the result in `DERIVED_ISSUE_NUMBER` (empty string if none found):

```bash
DERIVED_ISSUE_NUMBER=""  # set this to the issue number you derived above, or leave empty
```

This variable is consumed by the parser block below to resolve the final
`ISSUE_NUMBER` when the user invokes `/review` without arguments.

Also parse `$ARGUMENTS` for the `--force-on-closed` flag:

```bash
ARGS=( $ARGUMENTS )
FORCE_ON_CLOSED=false
PARSED_ISSUE=""
for arg in "${ARGS[@]}"; do
  case "$arg" in
    --force-on-closed) FORCE_ON_CLOSED=true ;;
    *)
      stripped="${arg##\#}"
      if [[ "$stripped" =~ ^[0-9]+$ ]]; then
        PARSED_ISSUE="$stripped"
      fi
      ;;
  esac
done
ISSUE_NUMBER="${PARSED_ISSUE:-$DERIVED_ISSUE_NUMBER}"  # context-derived takes second place
```

## 0.1a: Gate: issue state

> Mirrors the gate in `define.md` / `design.md` / `implement.md` / `review.md`.
> When editing this gate, update all four files in lockstep.

This gate **aborts** the skill if the linked GitHub issue is CLOSED, unless
the operator passes `--force-on-closed`. It runs **after** issue-context
detection (0.1) and **before** any side-effecting step (0.2 onward — make
check, branch cuts, push, PR creation, label changes, merge).

### `/review`-specific clause: skip silently when no issue is derivable

If 0.1 produced no `ISSUE_NUMBER` (no progress file, no `Closes #N` in PR
body, no inferable issue from branch/commits), **skip this gate silently** —
no abort, no warning. This preserves today's behavior for issue-less
reviews. Proceed directly to 0.2.

### State + closed-by lookup (single call)

When `ISSUE_NUMBER` is non-empty:

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
  - Perform **no further actions** — do not run `make check`, do not push,
    do not create a PR, do not change labels, do not merge.
  - Stop the skill (return non-zero).
- Else: proceed to 0.2.

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

## 0.2: Verify pre-PR gate

```bash
make check
```

## 0.3: Branch base — cut from freshly-fetched origin/main (when creating a new branch)

If `/review` is invoked without a pre-existing feature branch (i.e., this flow
will create one), apply the same invariant as `/implement`: cut from a
freshly-fetched `origin/main`, never stale local `main`.

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

## 0.4: Push and create PR

```bash
git push -u origin HEAD
gh pr create --repo "$REPO" --title "<title>" --body "$(cat <<'EOF'
Closes #<issue-number>

## Summary
<brief description>

## Test Plan
- [x] `make check` passed
- [ ] CI passes
- [ ] Docker health check passes
EOF
)" --label "ai:autonomous"
```

---

# Phase A: Gate Check

## A.1: CI checks

```bash
gh pr checks <number> --repo "$REPO"
```

Wait for CI to complete. If checks fail, fix and push.

## A.2: No blocking labels

Check for `review:changes-requested` or `review:pending` labels.

---

# Phase B: Autonomous Eng-Committee Code Review Loop

```
ROUND = 0
MAX_ROUNDS = 3
```

## Loop

### B.1: Read the full PR diff

```bash
gh pr diff <number> --repo "$REPO"
```

### B.2: Each committee member reviews through their code-review lens

Read `docs/developer/code-review-lenses.md` for role definitions.
Each committee member (per manifest review order) reviews the diff, categorizing findings as MUST-FIX, SHOULD-FIX, or NIT.
Post each review as a PR comment.

### B.3: Engineering Manager synthesizes

Collect all MUST-FIX and SHOULD-FIX items. NITs noted but don't block.
If zero MUST-FIX and zero SHOULD-FIX, break out of loop.

### B.4: Apply fixes

Fix items, run `make check`, commit, push.

### B.5: Focused re-review

On subsequent rounds, only affected members re-review new commits.

## Loop exit

Engineering Manager posts APPROVED sign-off comment. If MAX_ROUNDS reached with MUST-FIX,
create follow-up issues but don't block merge.

---

# Phase C: Merge & Deploy

## C.1: Merge

```bash
gh pr merge <number> --repo "$REPO" --squash --admin
```

## C.2: Label transitions

```bash
gh label create "merged" --color "6e5494" --repo "$REPO" 2>&1 | grep -v "already exists" || true
gh issue edit <issue-number> --repo "$REPO" --add-label "merged" --remove-label "implementing"
```

## C.3: Docker deployment verification

```bash
docker compose up --build -d
curl -sf http://localhost:8000/healthz
```

## C.4: Rollback (if deployment fails)

```bash
docker compose down
git revert HEAD --no-edit
git push
docker compose up --build -d
```

---

# Phase D: Report

## D.1: Close linked issue

```bash
gh issue comment <issue-number> --repo "$REPO" --body "Resolved via PR #<number>."
gh issue close <issue-number> --repo "$REPO"
```

## D.2: Final report

Summarize: merge SHA, review rounds, fixes applied, deploy status, follow-up issues.
