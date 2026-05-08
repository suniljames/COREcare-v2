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
