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

Read the PRD template from `docs/developer/prd-template.md`.

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
