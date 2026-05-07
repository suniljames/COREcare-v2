# PHI Redaction Checklist

> Read [`INVESTIGATIONS.md`](INVESTIGATIONS.md) first for context.

This checklist is the **mandatory pre-crawl gate** for [#107](https://github.com/suniljames/COREcare-v2/issues/107). Every category below must be verified yes/no/N/A on a representative sample of v1 pages **before** the authoritative crawl runs and **before** any screenshot is committed to v2's git history.

The committed catalog runs against a **PHI-scrubbed seed fixture** (`~/Code/COREcare-access/fixtures/v2_catalog_snapshot.json`). All field values must come from the locked PHI placeholder set documented in [`docs/migration/README.md` §PHI Placeholder Convention](../../docs/migration/README.md). **Faker-generated values are not acceptable.**

---

## Verification methodology

### Sampling

Before the authoritative crawl, run a manual **PHI spike**:

1. Bring v1 up with the PHI-scrubbed fixture loaded.
2. Pick 5 routes per persona (Super-Admin, Agency Admin, Care Manager, Caregiver, Family Member — Client persona omitted per `INVESTIGATIONS.md`). Total 25 routes.
3. Sample each route at desktop viewport in a real browser.
4. Walk through the checklist below for every screenshot. Record yes/no/N/A + verification note for every category.
5. **If any category fails on any image:** stop. Fix the seed fixture. Reload, re-spike. Do not proceed to the authoritative crawl until the spike passes 100%.

After the authoritative crawl, run a **post-crawl audit**:

6. Sample 10% of all committed images (cap 100) using `random.seed(42)` over the file list.
7. Re-walk every category. Same yes/no/N/A discipline. Commit the audit artifact (`PHI-AUDIT-<DATE>.md`) alongside the catalog.

Manual is the right answer here — automated PHI detection is unreliable for free-text content (chart notes, internal messages, addresses with apartment numbers). A human auditor is the only acceptable gate.

### What "fails" means

A category fails if **any committed image** displays:
- Real-or-realistic-looking PHI (Faker output, leftover dev data from a non-fixture state, scraped-from-elsewhere placeholder data that resembles actual people).
- Placeholder text that *looks* like real data to a casual reader (e.g., a chart note that reads like prose rather than `[NOTE_TEXT]`).
- Contextual leakage that, combined with public information, could re-identify an individual.

A category passes if every committed image displays:
- Locked PHI placeholders (`[CLIENT_NAME]`, `[ADDRESS]`, etc.) verbatim, OR
- Empty states ("No clients yet"), OR
- Visibly-synthetic values that no reasonable person would mistake for real PHI (e.g., names along the lines of `test-user-1`, `test-user-2`).

`N/A` applies when a category does not appear on any image in the sample (e.g., no images contain DOB displays).

---

## The 11 categories

For each: rule, why it matters, sample audit log entry.

### 1. Names (clients, caregivers, family members, care managers, agency staff)

**Rule:** every name displayed on any committed image must be from the locked placeholder set: `[CLIENT_NAME]`, `[CAREGIVER_NAME]`, `[CARE_MANAGER_NAME]`, `[FAMILY_MEMBER_NAME]`, `[AGENCY_ADMIN_NAME]`, `[SUPER_ADMIN_NAME]`. No first-last-name-shaped values.

**Why:** the most common PHI-leak vector. A name + a city = re-identification.

**Sample audit log entry:**
```
| 1. Names | yes | reviewed all 25 spike screenshots, every personally-identifying name field renders [CLIENT_NAME] or [CAREGIVER_NAME] or other locked placeholder |
```

### 2. Addresses (street, city, state, ZIP, geolocation lat/lon)

**Rule:** any address shown must be `[ADDRESS]` for the street/line2 fields. `[CITY]`, `[STATE]`, `[ZIP]` for geo components. Latitude/longitude must be either absent, zero, or visibly-synthetic non-real coordinates (e.g., `0.0, 0.0`).

**Why:** a real ZIP + a real DOB-quartile is enough for re-identification.

**Note:** v1's `Client` model has `latitude` / `longitude` for geofencing. The fixture sets these to a non-real value (e.g., `0.0, 0.0` or a verifiable test fixture point) and the catalog README documents the coordinate convention.

### 3. Phone numbers

**Rule:** phone numbers must be `[PHONE]` literally (preferred) or US phone numbers in the [555-xxx-xxxx test range](https://en.wikipedia.org/wiki/555_(telephone_number)) (`555-0100` through `555-0199` are reserved for fictional use). Real-shaped numbers (any other 555 prefix or any non-555 area code) are forbidden.

**Why:** fictional 555 ranges are a recognized convention; arbitrary digits read as real.

### 4. Email addresses

**Rule:** emails must use a non-existent domain. Acceptable: `<placeholder>@example.com`, `<placeholder>@test.com`, `<placeholder>@example.invalid`. Domains in the IANA-reserved test set (`example.com`, `example.org`, `example.net`, `*.test`, `*.invalid`, `*.localhost`) are safe. Domains that resolve to real email providers (`gmail.com`, `bayareaelitehomecare.com`, `mail.com`) are forbidden.

**Why:** a real-domain email + a name is a deliverable spam target and a re-identification handle.

### 5. Dates of birth

**Rule:** every DOB displayed must be either `[CLIENT_DOB]` literally (preferred) or a deterministic test value visibly outside any plausible real range (e.g., `1900-01-01` for all clients in the fixture). Faker output (e.g., `1962-04-12`) is forbidden — DOB has high re-identification power even alone.

**Why:** DOB + state + sex is sufficient to re-identify ~87% of US individuals (Sweeney 2000).

### 6. MRN / chart numbers / internal IDs

**Rule:** chart numbers, medical record numbers, and any internal patient-identifying ID must be sequential test values (`1`, `2`, `3`, ...) or use the `[MRN]` placeholder. v1 doesn't use real-shaped MRNs (no Epic-style 8-digit MRNs surfaced in the inventory), but capability-gated `chart_number` fields exist on some models — confirm the fixture sets them to placeholders.

### 7. Insurance IDs / policy numbers

**Rule:** if any insurance / policy field appears, the value must be a placeholder (`[INSURANCE_ID]`) or empty. v1 may not display these; verify on the spike.

### 8. Prescription / medication names + dosages

**Rule:** medication names rendered on chart-note pages or medication-orders pages must come from the placeholder set: `[MEDICATION]` (literal) or a known-fictional list (e.g., `Test-Med-A`, `Test-Med-B`). Dosages: `[DOSAGE]` or `Xmg twice daily` patterns that don't correspond to real prescribing schedules. Real medication-name+dose combinations leak diagnostic information.

### 9. Diagnosis codes / ICD codes / care-plan diagnosis text

**Rule:** diagnosis fields must use `[DIAGNOSIS]` placeholder text. ICD codes that look real (e.g., `I10` for hypertension) leak diagnosis information; use `[ICD_CODE]` instead.

### 10. Photographs / avatars / profile images

**Rule:** every committed image must show either:
- A blank avatar (default Django/v1 silhouette), OR
- A solid-color or abstract placeholder image, OR
- A clearly-synthetic test image (e.g., a checkered pattern, a labeled placeholder image)

Real photographs of any human face are forbidden. v1's `Client` and `CaregiverProfile` models have `photo` fields — fixture must leave them null (which renders the default silhouette).

### 11. Free-text fields (chart notes, internal messages, expense descriptions, care-plan notes, visit summaries)

**Rule:** the highest-leak surface. Free text has no schema; any string can sneak through. Two acceptable strategies:

a. **Placeholder text only:** the literal string `[NOTE_TEXT]` or `[MESSAGE_TEXT]` populates every free-text field. Easy to verify; loses visual fidelity.

b. **Synthetic prose with no PHI signature:** carefully-authored generic content that doesn't reference names, places, dates, conditions, or medications. Example acceptable: *"Visit went smoothly. Client reported feeling well. Reviewed care plan goals."* Example forbidden: any sentence that names a specific person plus a street address plus a symptom plus a time — even with placeholder values, that combination is a PHI-shaped pattern that erodes the auditor's signal-to-noise ratio.

If using strategy (b), the catalog operator commits the source text alongside the fixture for auditor review. Strategy (a) is the safer default unless the visual fidelity is required for catalog usefulness.

**Verification at spike time:** read every visible free-text string on every spike screenshot. If anything reads like a real-world note, fail.

---

## Audit-log template

For the spike (pre-crawl) and the 10% post-crawl audit, commit a Markdown table in `PHI-AUDIT-<DATE>.md`:

```markdown
# PHI Audit — <YYYY-MM-DD>

**Scope:** <e.g., 25-image pre-crawl spike / 10% post-crawl sample (60 images)>
**Sampling seed:** <e.g., random.seed(42) over file list at git ref abc123>
**Auditor:** <name>
**v1 commit:** 9738412a6e41064203fc253d9dd2a5c6a9c2e231
**Fixture sha256:** <hash>

| # | Category | Verdict | Note |
|---|----------|:-------:|------|
| 1 | Names | yes | All names render [CLIENT_NAME] / [CAREGIVER_NAME] / etc. across all sampled screenshots. |
| 2 | Addresses | yes | All address fields show [ADDRESS] / [CITY] / [STATE] / [ZIP]. Lat/lon = 0.0, 0.0 on Client geofence map. |
| 3 | Phone numbers | yes | All phones show [PHONE] or 555-01XX. |
| 4 | Email addresses | yes | All emails use @example.com or @test.com. |
| 5 | Dates of birth | yes | All DOBs show 1900-01-01 in the fixture. |
| 6 | MRN / chart numbers | N/A | No chart-number field rendered in this sample. |
| 7 | Insurance IDs | N/A | No insurance field rendered in this sample. |
| 8 | Medications | yes | Chart-orders page renders [MEDICATION] in 4 places. |
| 9 | Diagnosis codes | yes | Care-plan diagnosis field renders [DIAGNOSIS]. |
| 10 | Photographs / avatars | yes | All avatars show default silhouette. No client photos. |
| 11 | Free-text fields | yes | Chart notes / messages render [NOTE_TEXT] / [MESSAGE_TEXT]. No prose-shaped content. |

**Verdict:** PASS — proceed with authoritative crawl. *or* FAIL — stop, fix fixture, re-spike.
```

If FAIL: the line item is corrected on the seed fixture, the spike is re-run end-to-end (not just on the failed item — fixture changes can ripple).

---

## What this checklist does not cover

- **Dynamic content from external systems:** the v1 dev DB is local SQLite + the loaded fixture; no external system writes data into it. If the catalog operator deviates (e.g., loads production-derived data into a dev DB), this checklist does not protect them.
- **Backend logs / API responses:** the catalog captures rendered HTML pages. JSON API responses to admin tools (`?format=json`) are not screenshotted by default — the inventory excludes JSON-only routes per `docs/migration/README.md` rules. If the spike encounters an HTML page that surfaces JSON inline (e.g., a diagnostic page printing raw JSON), audit it under category 11.
- **Image metadata (EXIF):** WebP encoding strips EXIF by default with `sharp`. The fixture's photo fields are null, so this is moot for the catalog, but the crawler README documents the EXIF-strip default for future contributors.
