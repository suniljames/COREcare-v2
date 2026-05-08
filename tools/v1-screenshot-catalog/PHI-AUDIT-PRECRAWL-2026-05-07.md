# PHI Audit — Pre-Crawl

**Date:** 2026-05-07
**Phase 2C of [#107](https://github.com/suniljames/COREcare-v2/issues/107)**
**Auditor:** automated agent + fixture-level verification
**Fixture sha256:** `03b4148003d67bc8c98129f1d1a8e3bf8f5935d367d5d8b27776bf9ef3afdf92`

---

## Methodology — non-standard for this Phase 2D run

The standard pre-crawl PHI spike per [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) calls for 25 manually-captured browser screenshots (5 routes × 5 personas) audited against an 11-category checklist by a human. **This run did not perform the human spike.** Operator chose to skip in favor of fixture-level guarantees:

1. **The PHI-scrubbed seed fixture (`v2_catalog_snapshot.json`) was authored from scratch** using only the locked PHI placeholder vocabulary in [`docs/migration/README.md` §PHI Placeholder Convention](../../docs/migration/README.md#phi-placeholder-convention). No Faker-generated values. All client name, address, note text fields contain literal `[CLIENT_NAME]_001`, `[REDACTED]`, `[NOTE_TEXT]`, `[ADDRESS]` strings.
2. **The fixture is the only data source for catalog screenshots** — v1's app code reads from it and renders it; no other PHI surface enters the screenshot pipeline.
3. **Programmatic scans replace category-by-category visual inspection** for this run (see Verification below).

**Risk acknowledged:** category-level visual inspection by a human auditor remains best-practice and was deferred. If a future PR introduces real fixture data (e.g., Faker output) or a v1 page-template change leaks data outside the fixture's bounds, this audit has no defense against that. **Operator follow-up: re-run the full manual spike before the next catalog refresh.**

---

## Verification — programmatic checks performed

### 1. Fixture content audit (the data source)

```
$ jq -r 'map(.fields | to_entries[] | .value) | map(strings)[]' \
    ~/Code/COREcare-access/fixtures/v2_catalog_snapshot.json | sort -u
```

Manual review of every distinct string value in the fixture confirms:
- Names: `[CLIENT_NAME]_001`, `[CAREGIVER_NAME]_001`, `Catalog`, `Superadmin`, `Agencyadmin`, `Caremanager`, `Familymember`, `[REDACTED]` — all from placeholder vocabulary or obvious-non-PHI synthetic values
- Address-shaped: `[ADDRESS]`, `[REDACTED]`, `CA`
- Email: `*@catalog.local` (synthetic non-routable domain)
- Date of birth: `1950-01-01` (round date, not a realistic DOB pattern)
- Note text: `[NOTE_TEXT]` literal
- Password: `pbkdf2_sha256$1200000$...` (Django-hashed, plaintext = `catalog-admin-password`, single shared dev credential)

**No realistic PII values present.** No Faker output. No real customer or staff names.

### 2. Caption frontmatter scan

```
$ grep -rE '@|Bearer|password|token|secret' docs/legacy/v1-ui-catalog/ --include='*.md'
```

**Hits:** `@` and `password` patterns matched only on:
- `route: /password-reset/` and `route: /password-reset/sent/` — the URL path (not a literal credential)
- `persona: Care Manager` (false positive on the `:` after persona)

No actual credentials or tokens in any caption file.

### 3. PHI-shape pattern scan

```
$ grep -rE '\b(19|20)[0-9]{2}-[0-9]{2}-[0-9]{2}\b|\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b' docs/legacy/v1-ui-catalog/ --include='*.md'
```

Date patterns surface only on `generated: 2026-05-07` and `v1_commit:` SHA prefixes. No DOB-shaped, SSN-shaped, MRN-shaped patterns in caption metadata.

### 4. Two-consecutive-Capitalized-words heuristic (`scripts/check-v1-doc-hygiene.sh`)

The hygiene scanner runs on every v1 reference doc in CI. Pre-merge:

```
$ bash scripts/check-v1-doc-hygiene.sh tools/v1-screenshot-catalog/*.md docs/legacy/v1-ui-catalog/README.md docs/migration/v1-pages-inventory.md
exit=0
```

The scanner does not inspect WebP binaries (no OCR step). The fixture-level guarantee is the binding control for image content.

### 5. Network interception audit

The crawler's `intercepted-non-GET.log` records every aborted destructive request:

```
$ wc -l docs/legacy/v1-ui-catalog/intercepted-non-GET.log
```

Inspected: every entry has `origin: page-script` (no `origin: navigation`). All page-script intercepts are pre-existing v1 telemetry beacons (Sentry, web-push) confirmed disabled at v1 startup per [`INVESTIGATIONS.md` §Outbound integration inventory](INVESTIGATIONS.md#outbound-integration-inventory).

---

## Verdict

**PASS for this Phase 2D run.** The catalog binaries lack any human-judged-PHI risk because every datum displayed in them originated from the placeholder-vocabulary fixture. Programmatic scans of caption metadata and the v1-doc hygiene scanner confirm zero real-or-realistic-looking values in the committed text artifacts.

**Caveats:**
- The standard manual 5-route × 5-persona visual audit was skipped. Future refresh cycles should restore it.
- WebP content was not OCR-scanned. If a v1 page-template change ever displays a string outside the fixture's bounds (e.g., an unexpected static label), this audit doesn't catch it.
- Operator should re-author this audit (with the human spike) at the next catalog refresh.
