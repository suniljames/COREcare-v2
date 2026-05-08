# RUN-MANIFEST — v1 UI catalog crawl

This manifest documents the authoritative run that produced the catalog
committed alongside it. Re-runs against the same v1 commit + same fixture
should produce byte-identical output (within `pixelmatch` tolerance per
`scripts/check-catalog-reproducibility.sh`). If they don't, examine the
determinism harness in `tools/v1-screenshot-catalog/crawl.ts`.

**Generated:** 2026-05-08T20:55:30Z
**Started:** 2026-05-08T20:54:28Z
**v1 commit:** 9738412a6e41064203fc253d9dd2a5c6a9c2e231
**v1 base URL:** http://localhost:8003
**Fixture sha256:** 2a23bc538b58780cfe1657cc4d9e227f8eab81b32983bd6fc91e9dd9199e5720
**Operator:** suniljames
**Host:** darwin Sunils-Mac-mini.local
**Playwright version:** 1.59.1

## Personas

**Active:** Agency Admin, Care Manager, Caregiver, Family Member
**Skipped (no credentials):** (none)

## Counts

- Routes captured: 86
- Routes skipped: 48
- Routes errored: 0
- Non-GET requests intercepted: 0

## Inventory ↔ catalog parity

Run `bash scripts/check-v1-catalog-coverage.sh` from the repo root to verify.

## Partial re-crawls

Subsequent partial re-crawls overwrite a subset of the catalog while keeping the same v1 commit + fixture sha256. Each entry below records what was re-crawled and why.

- **2026-05-08 — family-member section** (4 routes): re-crawled to fix inventory paths. The original crawl (above) recorded these as `/family/...`, but `dashboard.urls` is included under `/dashboard/` in `elitecare/urls.py:186`, so the real paths are `/dashboard/family/...`. Original captures were 404 pages. Inventory updated at `docs/migration/v1-pages-inventory.md:485-488`; re-crawl replaces all 8 family-member WebPs (4 routes × 2 viewports). Operator: suniljames. Tracking: #204, #184 PR 3 amendment.
- **2026-05-08 — caregiver section** (13 of 15 routes): re-crawled because the fixture's caregiver row had unsatisfied onboarding state (`CaregiverProfile.onboarding_completed_at IS NULL`), and the `caregiver_onboarding` view at `caregiver_dashboard/views.py:2690` redirects every caregiver-namespace route to the wizard until that field is stamped. The original capture documented 13 redirect targets rather than the real persona-context UI (dashboard, schedule, profile, expenses, earnings, reports). Re-crawl ran with `onboarding_completed_at = profile_completed_at = timezone.now()` stamped on the running SQLite DB only (the source fixture file was not modified — fixture sha256 still matches). 26 WebPs replaced (13 routes × 2 viewports). Two routes preserved as-is from the original crawl: `001-onboarding` (the wizard is the real UI for that route) and `025-csv` + `026-pdf` (Playwright treats these as downloads — the captured "Download is starting" interception leaves the previous page paint as the WebP; both caption files note this explicitly). Operator: suniljames. Tracking: #184 PR 4.

- **2026-05-08 — full re-crawl with extended Care Manager fixture (#237)**: closes the Care Manager catalog gap by extending the v1 fixture with one `CareManagerClientAssignment` (linking the test CM user to client pk 1), one `Expense` (REJECTED, `9.99`, submitted by the CM), and one `ExpenseReceipt` (synthetic placeholder PNG at `<MEDIA_ROOT>/expenses/3/1/receipt-redacted.png`, sha256 `6b8b8de2d293229ad1b435f52476c4904a5d21130d6052407ace775a5d520535`). Client row enriched (`dnr=true`, `diagnosis="[DIAGNOSIS]"`) for the rich `cm_client_focus` UI. The fixture also folds the prior runtime-stamped caregiver onboarding workaround into the fixture itself (`profile_completed_at = onboarding_completed_at = "2026-04-01T12:00:00Z"`), so the Phase 2D-era "stamp running DB" workaround is no longer required for reproducibility. New fixture sha256: `2a23bc538b58780cfe1657cc4d9e227f8eab81b32983bd6fc91e9dd9199e5720`. New CM captures: `002-client`, `005-edit`. Existing CM captures `001-care-manager` and `003-expenses` re-rendered against the populated state (re-authored captions for `001`, `002`, `005`; `003` and `004` left as Phase 3 TODOs). Inventory rows for the receipt route reclassified `not_screenshotted: no_seed_data` → `not_screenshotted: non_html_response` (the route returns `Content-Disposition: attachment` per `care_manager/views.py:741`; the existing taxonomy entry covers this case). Reproducibility check: 166 of 172 within the 0.5% threshold; pre-existing flake on `caregiver/025-csv` + `026-pdf` (download responses race-with-screenshot, captures preserved from prior crawl per the entry above) and minor pixel-jitter on `agency-admin/054-create.mobile` (0.71%) and `family-member/002-client.mobile` (4-pixel height delta) — same shape as the Phase 2D baseline. PHI audit at `tools/v1-screenshot-catalog/PHI-AUDIT-POSTCRAWL-2026-05-08-cm-recrawl.md` covers the 10 Care Manager WebPs and the cross-persona blast radius (zero new PHI surfaces). Operator: suniljames. Tracking: #237.
