Evaluate a GitHub issue as a senior product manager and post a PRD as a comment.

## Repo Detection

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
```

Validate: if `$REPO` is empty or does not contain `/`, abort with:
> "Could not detect repository from git remote. Run this from inside the COREcare-v2 repo."

Use `--repo "$REPO"` on every `gh` command.

## Persona

Read the [PM persona](https://github.com/suniljames/directives/blob/main/teams/engineering/personas/pm.md).

Read `.claude/pm-context.md` for domain context (in-home medical care, HIPAA,
multi-tenant SaaS, care workflows, compliance requirements, stakeholder personas).

## Determine the issue

If `$ARGUMENTS` contains an issue number, use it. Otherwise, infer the issue
from the current conversation context. If you cannot confidently identify the
issue, resolve the ambiguity yourself using product judgment.

## Gate: issue state

> Mirrors the gate in `define.md` / `design.md` / `implement.md` / `review.md`.
> When editing this gate, update all four files in lockstep.

This gate **aborts** the skill if the GitHub issue is CLOSED, unless the
operator passes `--force-on-closed`. It runs **after** issue determination
and **before** any side-effecting step (label adds, comment posts, worktree
creation, branch cuts).

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
issue from "Determine the issue" above.

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
  - Perform **no further actions** — do not add labels, post comments, create
    worktrees, or cut branches.
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

## Step 1: Check idempotency

Check if the `pm-reviewed` label already exists on the issue:

```bash
gh issue view <number> --repo "$REPO" --json labels --jq '.labels[].name' | grep -q "pm-reviewed"
```

If the label exists, overwrite with a new PRD (autonomous mode — no confirmation needed).

## Step 2: Read the issue

Fetch the full issue (title, body, labels, linked issues, existing comments):

```bash
gh issue view <number> --repo "$REPO" --comments
```

## Step 3: Research related issues

1. **All open issues:**
   ```bash
   gh issue list --repo "$REPO" --state open --limit 200 --json number,title,labels,body
   ```

2. **Keyword-search closed issues:**
   ```bash
   gh search issues "<keywords>" --repo "$REPO" --state closed --limit 50 --json number,title,url
   ```

3. Build a list of related issues categorized as:
   - **Prerequisite** — must be done before this issue
   - **Related** — overlapping scope or same feature area
   - **Follow-up** — natural next step after this issue

## Step 4: Write the PRD

Read the [PRD template](https://github.com/suniljames/directives/blob/main/teams/engineering/process/prd-template.md).

Compose the PRD using that template with the persona context from
`.claude/pm-context.md`. Every section is **required** — use "N/A" with a
brief rationale if a section does not apply.

## Step 5: Post the PRD

```bash
gh issue comment <number> --repo "$REPO" --body "$(cat <<'EOF'
<PRD content here>
EOF
)"
```

## Step 6: Label the issue

```bash
gh label create "pm-reviewed" --color "6f42c1" --description "PRD posted by PM review" --repo "$REPO" 2>&1 | grep -v "already exists" || true
gh issue edit <number> --repo "$REPO" --add-label "pm-reviewed"
```

## Step 7: Report

Log the PRD posting and related issues found. Proceed directly to `/design`.
