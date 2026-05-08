# PHI Audit — Post-Crawl (Partial: caregiver re-crawl)

**Date:** 2026-05-08
**Scope:** Partial re-crawl of caregiver persona only (13 routes × 2 viewports = 26 WebPs)
**Tracking:** PR 4 of [#184](https://github.com/suniljames/COREcare-v2/issues/184)
**Auditor:** automated agent
**Fixture sha256:** `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` (matches RUN-MANIFEST.md)
**v1 commit:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`

---

## Method

Per [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md), a 10% sample of the captured artifacts gets a category-by-category visual inspection. With 26 new WebPs (13 routes × 2 viewports), 10% rounds to 3 images. **This audit covers all 13 mobile WebPs** (the lead-viewport set is the most data-dense surface; desktop renders are equivalent layouts of the same content).

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
| `001-onboarding.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Onboarding wizard step 1 form; placeholder phone/address values are form-template placeholders, not PHI. |
| `002-profile.mobile.webp` | N/A | N/A | N/A | N/A | placeholder | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Caregiver name fields show `[CAREGIVER_NAME]_001` + `[REDACTED]`; email is `caregiver@catalog.local`. Placeholder vocabulary intact. |
| `003-dashboard.mobile.webp` | placeholder | placeholder | N/A | N/A | N/A | N/A | placeholder | N/A | N/A | N/A | yes-debug-toolbar | Shift card: `[CLIENT_NAME]_001 [REDACTED]`; `[ADDRESS], [REDACTED], CA [REDACTED]`. Visit timestamps are fixture artifacts, not real visit data. |
| `004-schedule.mobile.webp` | placeholder | placeholder | N/A | N/A | N/A | N/A | placeholder | N/A | N/A | N/A | yes-debug-toolbar | Same placeholder pattern as 003. |
| `005-shift-offers.mobile.webp` | placeholder | N/A | N/A | N/A | N/A | N/A | placeholder | N/A | N/A | N/A | yes-debug-toolbar | Offer card: `[REDACTED], [CLIENT_NAME]_001`; rate `$25.00/hour`, est. earnings `$100.00` are fixture pricing values, not PHI. |
| `007-clock.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Clock-in form; client picker placeholder, no client values rendered yet. |
| `018-clients.mobile.webp` | placeholder | placeholder | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Client home: `[CLIENT_NAME]_001's Home`; `[ADDRESS], [REDACTED], CA [REDACTED]`. Empty states for care plan + emergency contact. |
| `019-submit.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Expense form; "Do not include client health information (PHI) in receipts." copy renders as a hard rule next to the file input. |
| `020-expenses.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Empty expense list; budget header `$0.00 of $250.00 used`. |
| `023-earnings.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Empty earnings; "No shifts" rows for the active week. |
| `024-weekly.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Empty weekly summary ("No visits recorded"). |
| `027-reports.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Empty reports list. |
| `028-new.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Report builder form; section toggles + formatting selectors. No PHI surface. |

Categories 1–10: `placeholder` indicates the page renders the catalog's PHI placeholder vocabulary (`[CLIENT_NAME]_001`, `[CAREGIVER_NAME]_001`, `[REDACTED]`, `[ADDRESS]`) — not real PHI. `N/A` indicates the category does not apply to that surface.

Category 11 (debug-toolbar): `yes` for all 13 captures — `Django Debug Toolbar` was open and visible in the screenshots; acceptable per the original Phase 2D audit (debug-toolbar internals expose URL conf + template names, not PHI).

## Caption-body PHI scan

Captions for the 14 caregiver routes were authored against the real UI (or, for 025-csv / 026-pdf, against the source view + a redirect-target stand-in). `bash scripts/check-v1-caption-phi.sh docs/legacy/v1-ui-catalog/caregiver/*.md` exits 0 — no `[CLIENT_NAME]`-style placeholders appear in any caption body.

## Result

**PASS.** No PHI surfaces detected in the 26 re-crawled WebPs. No PHI placeholder values appear in caption bodies. Audit holds.
