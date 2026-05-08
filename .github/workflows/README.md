# Workflow conventions

## Git LFS posture

The v1 UI catalog under `docs/legacy/v1-ui-catalog/` is stored via Git LFS (see [ADR-010](../../docs/adr/010-v1-ui-catalog-storage.md)). To keep monthly LFS bandwidth well under the free-tier 1 GB quota, workflows that do not need to read the catalog binaries must skip LFS smudging.

`actions/checkout@v4` defaults to `lfs: false`, so omitting the key is sufficient. Workflows that touch the catalog and explicitly set `lfs: false` are belt-and-suspenders.

A workflow that legitimately needs the catalog binaries — e.g. a hypothetical visual-regression check — must declare why on the same line:

```yaml
- uses: actions/checkout@v4
  with:
    lfs: true  # rationale: visual diff requires the actual WebP bytes
```

`scripts/check-workflow-lfs-posture.sh` enforces this convention and runs in `make check`. Reviewers must reject any PR that flips `lfs: true` without a same-line `# rationale: <text>` comment.

See [`docs/operations/lfs-bandwidth-watch.md`](../../docs/operations/lfs-bandwidth-watch.md) for the operational runbook covering the 30-day watch period that follows the catalog merge.

## `issue_comment` triggers — three filter layers

Workflows triggered by `issue_comment` (e.g. `lfs-bandwidth-auto-closure.yml`) fire on every comment in every issue and PR repo-wide. Three filter layers narrow the scope, and **all three must be present**. Reviewers must reject any PR that loosens any layer without a security-review citation.

1. **Repo-level event filter** — `on: issue_comment: types: [created]`. Excludes `edited` and `deleted` so re-edits do not trigger duplicate side effects.
2. **Job-level `if:` condition** — must check both `github.event.issue.number == <N>` (scope to one issue) and `github.event.comment.user.type != 'Bot'` (skip bot-authored comments to prevent loops). Use the `.user.type` field rather than a hardcoded login string so the filter generalizes across GitHub bots (Copilot, Dependabot, future automations).
3. **Step-level matcher** — the workflow's first action step must validate the comment body against an anchored regex specific to its purpose (e.g., `scripts/lib/lfs-report-matcher.sh` anchors on `^**30-day Git LFS bandwidth report**`). Substring matches are not sufficient.

If a future workflow uses `issue_comment` and the resulting side effect is destructive (deleting files, opening PRs, closing issues, filing follow-ups), all three layers are mandatory. For read-only or low-risk side effects, layers (1) and (2) are still mandatory; (3) may be relaxed with explicit rationale in the workflow file's header comment.
