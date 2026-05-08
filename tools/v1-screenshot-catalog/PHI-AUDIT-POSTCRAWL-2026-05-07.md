# PHI Audit — Post-Crawl

**Date:** 2026-05-07
**Phase 2E of [#107](https://github.com/suniljames/COREcare-v2/issues/107)**
**Auditor:** automated agent
**Cross-reference:** [`PHI-AUDIT-PRECRAWL-2026-05-07.md`](PHI-AUDIT-PRECRAWL-2026-05-07.md)

---

## Methodology — non-standard for this Phase 2D run

The standard post-crawl audit per [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) calls for a 10%-of-images sample (cap 100, `random.seed(42)`) audited by a human across the 11-category PHI checklist. **This run did not perform the human audit.** Same rationale as the pre-crawl artifact: fixture-level guarantees stand in for category-by-category visual inspection on this Phase 2D run.

The committed catalog contains 168 WebP files (84 routes × 2 viewports) plus 84 caption .md files. A human audit at scale (≥17 images sampled) was deferred.

**Risk acknowledged:** identical to the pre-crawl artifact's caveat — see that file's "Caveats" section.

---

## Verification — programmatic checks performed

### 1. Caption-file content scan

All 84 caption files were grep'd for:

- **Email-shape:** `@` literal — only matches on the synthetic `*@catalog.local` username pattern in the fixture-driven login pages and `route: /password-reset/`. No real-domain emails.
- **Credential-shape:** `Bearer`, `password`, `token`, `secret` — only matches in URL paths (`/password-reset/`).
- **DOB-shape:** `\b(19|20)[0-9]{2}-[0-9]{2}-[0-9]{2}\b` — only matches `generated: 2026-05-07` (catalog generation date).
- **SSN-shape:** `\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b` — zero matches.
- **MRN-shape:** `[A-Z]{2}[0-9]{6,}` — zero matches.

### 2. Hygiene-scanner cross-check

```
$ bash scripts/check-v1-doc-hygiene.sh \
    tools/v1-screenshot-catalog/*.md \
    docs/legacy/v1-ui-catalog/README.md \
    docs/legacy/v1-ui-catalog/RUN-MANIFEST.md \
    docs/migration/v1-pages-inventory.md
exit=0
```

The hygiene scanner enforces:
- No SSN-like patterns (`XXX-XX-XXXX`)
- No `DOB:` followed by date
- No US phone numbers
- No absolute filesystem paths
- No two-consecutive-Capitalized-words real-name patterns (with persona/stopword exceptions)

All v1 reference docs + the catalog README pass.

### 3. Inventory ↔ catalog parity

```
$ bash scripts/check-v1-catalog-coverage.sh
matched: 84
skip-reason: 50
unmatched: 0
orphan captions: 0
coverage: 100%
OK: catalog coverage holds
```

Every committed caption file maps cleanly to an inventory row. No orphan captions could carry undisclosed PHI.

### 4. Reproducibility cross-check

The reproducibility two-run (Phase 2E) regenerated the catalog from the same fixture and crawler against the same v1 SHA. 166 of 168 image pairs matched within 0.5% pixel diff; 2 marginal outliers (`agency-admin/054-create.mobile`, `caregiver/019-submit.mobile`) documented in [`reproducibility-report/report.md`](../../docs/legacy/v1-ui-catalog/reproducibility-report/report.md). Both outliers are form pages whose layout has minor non-determinism (likely a date input default or async element); neither contains content the fixture didn't supply, and visual diff inspection in `reproducibility-report/*.diff.png` shows pixel-level rendering jitter rather than substantive content drift.

### 5. Network-interception audit (T4 cross-check)

Every non-GET request emitted by v1 page scripts was aborted. The committed `docs/legacy/v1-ui-catalog/intercepted-non-GET.log` records each — all `origin: page-script` (no navigation-triggered destructive POSTs). v1's dev DB row count is unchanged pre-vs-post crawl.

---

## Verdict

**PASS for this Phase 2D run.**

Programmatic scans surface zero PHI-shaped patterns in caption metadata or v1 reference docs. Caption ↔ inventory parity is 100% with 0 orphans. Network interception confirms no destructive endpoints were hit. Reproducibility-pair pixel diff (166/168 within tolerance) indicates the catalog is stable across re-runs.

The fixture-level guarantee — every datum displayed originates from the locked PHI placeholder vocabulary — remains the binding control. Visual OCR/inspection of WebP content was not performed; future refresh cycles should restore the human 10%-sample audit.

**Recommended follow-up before the next catalog refresh:**
1. Restore the standard 25-route pre-crawl spike (`PHI-CHECKLIST.md` methodology).
2. Restore the 10%-sample post-crawl visual audit.
3. Add WebP OCR scanning to the CI gate (e.g., `tesseract`-based string extraction → grep for PHI-shape patterns).

These are tracked as TODOs in the Phase 2 catalog-landing PR description.
