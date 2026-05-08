# RUN-MANIFEST — v1 UI catalog crawl

This manifest documents the authoritative run that produced the catalog
committed alongside it. Re-runs against the same v1 commit + same fixture
should produce byte-identical output (within `pixelmatch` tolerance per
`scripts/check-catalog-reproducibility.sh`). If they don't, examine the
determinism harness in `tools/v1-screenshot-catalog/crawl.ts`.

**Generated:** 2026-05-08T00:10:39.997Z
**Started:** 2026-05-08T00:09:38.088Z
**v1 commit:** 9738412a6e41064203fc253d9dd2a5c6a9c2e231
**v1 base URL:** http://localhost:8002
**Fixture sha256:** 03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92
**Operator:** suniljames
**Host:** darwin Sunils-Mac-mini.local
**Playwright version:** 1.59.1

## Personas

**Active:** Super-Admin, Agency Admin, Care Manager, Caregiver, Family Member
**Skipped (no credentials):** (none)

## Counts

- Routes captured: 85
- Routes skipped: 44
- Routes errored: 6
- Non-GET requests intercepted: 0

## Inventory ↔ catalog parity

Run `bash scripts/check-v1-catalog-coverage.sh` from the repo root to verify.
