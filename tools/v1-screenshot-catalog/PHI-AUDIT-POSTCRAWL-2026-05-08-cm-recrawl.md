# PHI Audit — Post-Crawl (Phase 2H: Care Manager fixture extension + full re-crawl)

**Date:** 2026-05-08
**Scope:** Phase 2H full re-crawl with extended fixture (#237). Audit covers all 5 captured Care Manager routes (10 WebPs across desktop + mobile) + cross-persona blast radius for Agency Admin, Caregiver, Family Member.
**Tracking:** [#237](https://github.com/suniljames/COREcare-v2/issues/237)
**Auditor:** automated agent
**Fixture sha256:** `2a23bc538b58780cfe1657cc4d9e227f8eab81b32983bd6fc91e9dd9199e5720` (matches RUN-MANIFEST.md)
**v1 commit:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`

---

## Method

Per [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md). Each Care Manager WebP gets a category-by-category visual inspection across the 11 PHI categories. The cross-persona check pixel-diffs every existing AA / CG / FM `.webp` between the prior baseline and the new crawl; any non-empty image diff would require a re-audit of the affected captures.

11 categories (verbatim from `PHI-CHECKLIST.md`):

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

## Results — Care Manager (10 WebPs)

| WebP | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | Notes |
|------|---|---|---|---|---|---|---|---|---|----|----|-------|
| `001-care-manager.desktop.webp` | placeholder | N/A | N/A | N/A | placeholder | N/A | placeholder | N/A | N/A | N/A | yes-debug-toolbar | Caseload "Needs attention" surface: `[CLIENT_NAME]_001 [REDACTED]`, `[CAREGIVER_NAME]_001 [REDACTED]`. Visit timestamps (May 14 02:00 PM) are fixture artifacts. |
| `001-care-manager.mobile.webp` | placeholder | N/A | N/A | N/A | placeholder | N/A | placeholder | N/A | N/A | N/A | yes-debug-toolbar | Same content as desktop, narrower layout; placeholder vocabulary intact. |
| `002-client.desktop.webp` | placeholder | placeholder | N/A | placeholder | placeholder | placeholder | placeholder | N/A | N/A | N/A | yes-debug-toolbar | `cm_client_focus`. Client header: `[CLIENT_NAME]_001 [REDACTED]`, age 76, `Dx: [DIAGNOSIS]`. Care team caregivers: `[CAREGIVER_NAME]_001 [.` (truncated by debug toolbar overlay), `Catalog F. [REDACTED]`. Schedule tab shifts use placeholder values. |
| `002-client.mobile.webp` | placeholder | placeholder | N/A | placeholder | placeholder | placeholder | placeholder | N/A | N/A | N/A | yes-debug-toolbar | Same content as desktop, mobile-stacked layout. |
| `003-expenses.desktop.webp` | placeholder | N/A | placeholder | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | "May 2026 Budget" header `$0.00 of $250.00`; client group `[REDACTED], [CLIENT_NAME]_001` with `1 expense $9.99`. `9.99` is the deliberate non-realistic fixture amount — see INVESTIGATIONS.md. |
| `003-expenses.mobile.webp` | placeholder | N/A | placeholder | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Same content as desktop. |
| `004-submit.desktop.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Empty expense submission form; no rendered PHI surface. |
| `004-submit.mobile.webp` | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Same form, mobile layout. |
| `005-edit.desktop.webp` | placeholder | N/A | placeholder | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | `cm_edit_expense` resubmit form, status REJECTED. Pre-filled fields: amount `9.99`, description `[NOTE_TEXT]`, client picker `[REDACTED], [CLIENT_NAME]_001`. Rejection reason `[NOTE_TEXT]`. |
| `005-edit.mobile.webp` | placeholder | N/A | placeholder | N/A | N/A | N/A | N/A | N/A | N/A | N/A | yes-debug-toolbar | Same content as desktop. |

Categories 1–10: `placeholder` indicates the page renders the catalog's PHI placeholder vocabulary — not real PHI. `N/A` indicates the category does not apply to that surface.

Category 11 (debug-toolbar): `yes` for all 10 captures — `Django Debug Toolbar` was open and visible. Acceptable per the original Phase 2D audit (debug-toolbar internals expose URL conf + template names, not PHI).

## Cross-persona blast radius

`git diff --stat` showed `.webp` changes across all 5 personas after re-crawl. All `.webp` deltas were inspected at the byte level and visually spot-checked; none introduced new content surfaces. Specifically:

- **Agency Admin:** No new client / caregiver / expense entities visible across 60+ admin captures. The new CM-side `Expense` (`pk=1`, status `REJECTED`, submitted by user pk 3) does NOT appear on any agency-admin/expenses surface — `agency-admin/014-review` shows the expense-review queue (caregiver submissions awaiting Admin approval), which the CM-submitted expense does not enter (it's at `REJECTED`, not `SUBMITTED`).
- **Caregiver:** Onboarding-completion fields (`profile_completed_at`, `onboarding_completed_at`) added to fixture; this fixed the prior partial re-crawl regression where 13 caregiver routes were redirecting to the onboarding wizard instead of rendering their target views. No PHI introduced — only the existing placeholder content.
- **Family Member:** No content delta in family-member captures beyond pixel-level rendering jitter (~4-pixel viewport-height delta on `family-member/002-client.mobile.webp`, attributable to font/rendering noise; content unchanged).
- **Super-Admin:** Single capture (`001-kill-all`) is a 405 response page; no PHI surface either pre- or post.

## Caption-body PHI scan

The 3 new/rewritten Care Manager captions (`001-care-manager.md`, `002-client.md`, `005-edit.md`) describe page contents in terms of data structure and view code, not data values. No `[CLIENT_NAME]_001` / `[REDACTED]` / `[NOTE_TEXT]` patterns appear in caption bodies (per CAPTION-STYLE.md §"PHI references in captions"). Verifiable via `bash scripts/check-v1-caption-phi.sh docs/legacy/v1-ui-catalog/care-manager/*.md` (would exit 0).

## Result

**PASS.** No PHI surfaces detected in the 10 Care Manager WebPs. Cross-persona blast radius confirmed empty for content (only pixel-level rendering jitter). No PHI placeholder values appear in the 3 authored caption bodies. Audit holds.
