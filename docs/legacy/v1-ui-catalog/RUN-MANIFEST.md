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

## Partial re-crawls

Subsequent partial re-crawls overwrite a subset of the catalog while keeping the same v1 commit + fixture sha256. Each entry below records what was re-crawled and why.

- **2026-05-08 — family-member section** (4 routes): re-crawled to fix inventory paths. The original crawl (above) recorded these as `/family/...`, but `dashboard.urls` is included under `/dashboard/` in `elitecare/urls.py:186`, so the real paths are `/dashboard/family/...`. Original captures were 404 pages. Inventory updated at `docs/migration/v1-pages-inventory.md:485-488`; re-crawl replaces all 8 family-member WebPs (4 routes × 2 viewports). Operator: suniljames. Tracking: #204, #184 PR 3 amendment.
