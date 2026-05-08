# PHI Audit — Post-Crawl (Partial: family-member re-crawl)

**Date:** 2026-05-08
**Scope:** Partial re-crawl of family-member persona only (4 routes × 2 viewports = 8 WebPs)
**Tracking:** [#204](https://github.com/suniljames/COREcare-v2/issues/204), amends PR 3 of [#184](https://github.com/suniljames/COREcare-v2/issues/184)
**Auditor:** automated agent
**Fixture sha256:** `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` (matches RUN-MANIFEST.md)
**v1 commit:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`

---

## Method

Per [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md), a 10% sample of the captured artifacts gets a category-by-category visual inspection. With 8 new WebPs (4 routes × 2 viewports), 10% rounds to 1 image. **This audit covers all 8 WebPs** (the partial re-crawl is small enough to inspect end-to-end).

The inspector walked each WebP through the 11 PHI categories from `PHI-CHECKLIST.md`:

1. Patient identifying info (real names, DOB, MRN, SSN)
2. Client demographic detail (address, phone, email, gender beyond persona)
3. Insurance / billing identifiers
4. Diagnoses, ICD codes, prescriptions, medication names
5. Caregiver real names, CV details, cert numbers
6. Care plan content (chart notes, assessments, goals)
7. Visit-level data (timestamps, geolocation, signature pads)
8. Messages between family/caregiver/staff (real conversation content)
9. PDF download contents (billing, health-report, schedule PDFs)
10. Audit-log surfaces (visible session activity, IP addresses)
11. Stack-trace / debug-toolbar info that leaks user/data context

## Results

| WebP | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | Notes |
|------|---|---|---|---|---|---|---|---|---|----|----|-------|
| `001-dashboard.desktop.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Shows `[CLIENT_NAME]_001 [REDACTED]` per fixture; `Django Debug Toolbar` visible (acceptable per fixture-level audit) |
| `001-dashboard.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Same |
| `002-client.desktop.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Rich page; all PHI fields use `[CLIENT_NAME]_001`, `[CAREGIVER_NAME]_001`, `[REDACTED]`, `[NOTE_TEXT]` placeholders |
| `002-client.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Same |
| `003-billing-pdf.desktop.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Plain text "No billing data available for this period." — no PHI surface |
| `003-billing-pdf.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Same |
| `004-health-report.desktop.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Plain text "There isn't enough recent health data..." — no PHI surface |
| `004-health-report.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Same |

Categories 1–10: `N/A` for all 8 captures (no PHI in any category). Category 11 (debug-toolbar): `yes` for the 4 dashboard/client captures — `Django Debug Toolbar` was open and visible in the screenshots; acceptable per the original Phase 2D audit (debug-toolbar internals expose URL conf + template names, not PHI).

## Caption-body PHI scan

Captions for the 4 family-member routes were re-authored against the real UI. `bash scripts/check-v1-caption-phi.sh docs/legacy/v1-ui-catalog/family-member/*.md` exits 0 — no `[CLIENT_NAME]`-style placeholders appear in any caption body.

## Result

**PASS.** No PHI surfaces detected in the 8 re-crawled WebPs. No PHI placeholder values appear in caption bodies. Audit holds.
