/summarize — Plain-language stakeholder summary for shipped work.

Produce a jargon-free summary of a merged PR and post it to the linked GitHub issue.

## Repo Detection

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
```

## Parse arguments

Parse `$ARGUMENTS` for PR number. If not found, infer from current branch.

## Gather Context

1. Fetch PR details (must be merged)
2. Resolve linked issues
3. Get file list and commit messages

## Analyze Changes

Map files to affected user roles:

| Directory pattern | Role |
|---|---|
| `api/app/routers/` | Depends on domain |
| `api/app/services/` | Depends on domain |
| `web/src/app/(dashboard)/` | Agency users |
| `web/src/app/(platform)/` | Super-admin |
| `web/src/app/(auth)/` | All roles |
| `web/src/components/` | Depends on usage |
| `docs/` | Documentation |

## Write the Summary

Template:

```
**What's New**
<One-line headline>

**Why It Matters**
<2-3 sentences, no jargon>

**What You Can Do Now**
- <Concrete capability>

**How to Use It**
1. <Browser step>

**Who This Affects**
- <Role>: <impact>

**What to Tell Your Team**
<Ready-to-forward message>

**Shipped in**
PR #<number> · Issue #<issue>
```

## Post

Post as issue comment, add `summarized` label.
