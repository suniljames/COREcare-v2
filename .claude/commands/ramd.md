/ramd — Review gates. Approve. Merge. Deploy.

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

## 0.2: Verify pre-PR gate

```bash
make check
```

## 0.3: Push and create PR

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
)" --label "ai:claude-code"
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

Read `.claude/commands/references/code-review-lenses.md` for role definitions.
Each of the 9 members reviews the diff, categorizing findings as MUST-FIX, SHOULD-FIX, or NIT.
Post each review as a PR comment.

### B.3: Judge synthesizes

Collect all MUST-FIX and SHOULD-FIX items. NITs noted but don't block.
If zero MUST-FIX and zero SHOULD-FIX, break out of loop.

### B.4: Apply fixes

Fix items, run `make check`, commit, push.

### B.5: Focused re-review

On subsequent rounds, only affected members re-review new commits.

## Loop exit

Judge posts APPROVED sign-off comment. If MAX_ROUNDS reached with MUST-FIX,
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
