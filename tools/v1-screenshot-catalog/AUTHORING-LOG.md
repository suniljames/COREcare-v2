# Authoring Log — v1 UI Catalog Phase 3 (#184)

> Read [`CAPTION-STYLE.md`](CAPTION-STYLE.md) §Authoring workflow first. This log is the operator's session record for the Phase 3 caption-authoring pass tracked in [#184](https://github.com/suniljames/COREcare-v2/issues/184).

## Purpose

Forensic ground truth for "which session, which fixture state, which persona section" if a caption is later questioned in review. One row per authoring session; commit each row at session start.

## Session log format

| Date | Start–end (PT) | Persona section | Captions touched | Fixture sha256 (precheck) | Operator | Notes |
|------|----------------|-----------------|------------------|---------------------------|----------|-------|
| YYYY-MM-DD | HH:MM–HH:MM | super-admin / agency-admin / care-manager / caregiver / family-member | NNN–NNN | `<sha256 from precheck output>` | suniljames | (anything atypical) |

## Sessions

<!-- Append session rows below this line. Do NOT delete prior rows; this is a permanent forensic record. -->

| Date | Start–end (PT) | Persona section | Captions touched | Fixture sha256 (precheck) | Operator | Notes |
|------|----------------|-----------------|------------------|---------------------------|----------|-------|
| 2026-05-08 | 18:30–18:55 | super-admin | 001 | `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` | suniljames | **Source-archaeology methodology** (no v1 server run): caption authored from WebP + v1 source at pinned commit `9738412a` (URL conf, view function, service method, template). Fixture sha verified against `RUN-MANIFEST.md` directly without invoking the precheck script (no localhost involved). Route `/admin/view-as/kill-all/` is POST-only with no GET handler — captured screenshots are the empty 405 response, so no UI to observe; behavior derived from `core/view_as_views.py:259` + `core/services/view_as_service.py:284`. |
| 2026-05-08 | 19:00–19:45 | care-manager | 001, 003, 004 | `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` | suniljames | **Source-archaeology methodology**. Read WebPs + `care_manager/views.py` + `care_manager/urls.py` + `templates/care_manager/*.html` at `9738412a`. Fixture's CM user has no assigned clients (verified by direct WebP inspection of 001 — empty state visible), so 001 captions describe the empty state honestly while noting the populated rendering for context. **Tooling fixes during authoring** (filed inline as part of this PR rather than blocking on follow-up issues): voice script + hygiene script both updated to strip `"..."` quoted runs before scanning content rules — literal v1 button labels (e.g., `"Submit your first expense"`, `"Submit Expense"`) legitimately contain "you/your" and bigram-capitalized words that previously tripped voice and plausible-name checks. Two new tests added to lock the new behavior. |
| 2026-05-08 | 20:00–20:50 | family-member | 001, 002, 003, 004 | `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` | suniljames | **Inventory-bug discovery**: all 4 family-member WebPs are Django `DEBUG=True` 404 pages. The inventory documented `/family/...` paths but `dashboard.urls` is included under `/dashboard/`, so real paths are `/dashboard/family/...`. Filed as #204; captions shipped describing the 404 + intended UI as a stand-in. |
| 2026-05-08 | 21:30–22:30 | family-member (re-crawl + re-author) | 001, 002, 003, 004 | `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` | suniljames | **Resolution of #204**: ran v1 locally on port 8002 (Django 6.0.2, DEBUG=True), verified the inventory mismatch with curl: `/family/dashboard/` returns 404, `/dashboard/family/dashboard/` returns 302 (login redirect, then real UI). Updated inventory paths at `docs/migration/v1-pages-inventory.md:485-488` (and the residual prose at line 494) to `/dashboard/family/...`. Re-ran the Phase 2 crawler scoped to family-member only (`pnpm crawl --output-dir /tmp/family-recrawl --only-personas family-member`), produced 8 real WebPs. Replaced the 404 captures + re-authored all 4 captions against real UI. RUN-MANIFEST.md updated with a partial-re-crawl note. v1 stopped after the crawl. |
| 2026-05-08 | 23:00–00:30 | caregiver (re-crawl + author) | 001, 002, 003, 004, 005, 007, 018, 019, 020, 023, 024, 025, 026, 027, 028 | `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92` | suniljames | **Live-UI methodology** (full v1 server bring-up): ran v1 on port 8002 with the catalog fixture loaded. Initial crawl returned the onboarding-wizard redirect for 13 of 15 caregiver routes because the fixture's `CaregiverProfile.onboarding_completed_at` was `NULL`. Stamped both `onboarding_completed_at` and `profile_completed_at` on the running SQLite DB (fixture file untouched), re-ran the crawler scoped to caregiver only (`pnpm crawl --output-dir /tmp/caregiver-recrawl-full --only-personas caregiver`), produced 26 real WebPs. Replaced 26 captures (13 routes × 2 viewports); preserved original captures for `001-onboarding` (wizard IS the real UI) and `025-csv` / `026-pdf` (Playwright download interception leaves the prior page paint as the WebP — caption files note this explicitly). Authored 14 captions against the real UI; 1 caption (001-onboarding) authored against the previously-correct wizard capture. New PHI-AUDIT artifacts added (`PHI-AUDIT-PRECRAWL-2026-05-08-caregiver-recrawl.md`, `PHI-AUDIT-POSTCRAWL-2026-05-08-caregiver-recrawl.md`) per the catalog-coverage gate's WebP-add → audit-required rule. RUN-MANIFEST.md updated. v1 stopped after the crawl. |

## Session-start checklist

For each new session row appended above:

1. ☐ `cd ~/Code/COREcare-access && git checkout 9738412a6e41064203fc253d9dd2a5c6a9c2e231`
2. ☐ Fresh SQLite DB (delete prior `.sqlite3` file)
3. ☐ `python manage.py migrate` exits 0
4. ☐ `python manage.py loaddata fixtures/v2_catalog_snapshot.json` exits 0
5. ☐ `bash scripts/v1-author-precheck.sh` exits 0 (record sha256 in row above)
6. ☐ `python manage.py runserver 0.0.0.0:8000` running
7. ☐ Session row committed before authoring starts

## Session-end checklist

For each completed session row:

1. ☐ `bash scripts/check-v1-doc-hygiene.sh <touched captions>` exits 0
2. ☐ `bash scripts/check-v1-caption-phi.sh <touched captions>` exits 0
3. ☐ `bash scripts/check-v1-caption-voice.sh <touched captions>` exits 0
4. ☐ `bash scripts/check-v1-catalog-coverage.sh` exits 0 (full catalog)
5. ☐ Captions touched committed
6. ☐ End time recorded in session row above
