Convene the engineering committee to review a GitHub issue.

## Repo Detection

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
```

Validate: if `$REPO` is empty or does not contain `/`, abort with:
> "Could not detect repository from git remote. Run this from inside the COREcare-v2 repo."

Use `--repo "$REPO"` on every `gh` command.

## Determine the issue

If `$ARGUMENTS` contains an issue number, use it. Otherwise, infer the issue
from the current conversation context.

## Lifecycle check: pm-reviewed

Check if the `pm-reviewed` label exists on the issue:

```bash
gh issue view <number> --repo "$REPO" --json labels --jq '.labels[].name' | grep -q "pm-reviewed"
```

If the label is **missing**, log a warning and proceed (autonomous mode).

## Idempotency check: design-complete

If `design-complete` label exists, overwrite with a new review (autonomous mode).

## Read the issue

```bash
gh issue view <number> --repo "$REPO" --comments
```

## Determine if UI/UX changes are involved

If the issue involves user-facing UI changes, UX Designer generates SVG mockups.
If purely backend/API/infra, skip mockups.

## Conduct the committee review

Follow the [committee process](https://github.com/suniljames/directives/blob/main/teams/engineering/process/committee-process.md):

1. **If UI/UX change:** UX Designer documents Design Direction and generates SVG mockups
   - Create `docs/mockups/<issue-number>/` directory
   - Generate high-fidelity SVGs consistent with `docs/design-system/`
   - Commit and push the SVGs
2. Each committee member posts their review **in review order** (per manifest), reading ALL prior comments
   - Post each review as a separate GitHub issue comment
   - **Committee is primed for FastAPI + Next.js 15 + shadcn/ui + PostgreSQL RLS + Clerk**
3. The Engineering Manager synthesizes all feedback into a final unified plan
4. **Overwrite-to-final-consensus:** Members whose positions changed overwrite their comments
   - QA Engineer overwrite rule: behavior changes only, not UI-treatment-only
5. Update the issue title and description to include:
   - Explanation for Hazel (non-technical, end-user value props)
   - Technical Details
   - Root Cause (if applicable)
   - Proposed Solution
   - Implementation Plan
   - Documentation Impact Assessment
   - Test Specification

## Fresh-Eyes Validation

Spawn a sub-agent to validate the issue description is self-contained:

1. All sections present and complete
2. No undefined terms
3. Test Specification is actionable
4. Implementation Plan has clear steps
5. Documentation Impact Assessment is explicit

Post validation result as an issue comment. If FAIL, fix gaps and re-validate.

## Label the issue

```bash
gh label create "design-complete" --color "0e8a16" --description "Eng-Committee design review complete" --repo "$REPO" 2>&1 | grep -v "already exists" || true
gh issue edit <number> --repo "$REPO" --add-label "design-complete"
```

## Proceed

Autonomous mode: proceed directly to `/implement`. No human checkpoint.
