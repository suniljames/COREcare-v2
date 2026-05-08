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
