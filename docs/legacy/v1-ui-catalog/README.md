# v1 UI Catalog — Index

> **This catalog operates against v1 (`hcunanan79/COREcare-access`).** v2 contributors browse the screenshots + captions here without ever needing v1 access. The crawler that produced these binaries lives at [`tools/v1-screenshot-catalog/`](../../../tools/v1-screenshot-catalog/) — read its [`README.md`](../../../tools/v1-screenshot-catalog/README.md) first if you want to understand how the catalog is generated or refresh it.

**Status:** AUTHORITATIVE. Phase 2D crawl ran on 2026-05-07 against v1 commit [`9738412a`](https://github.com/hcunanan79/COREcare-access/commit/9738412a6e41064203fc253d9dd2a5c6a9c2e231). Caption frontmatter is complete; caption bodies (CTAs visible + interaction notes) are tracked separately in the Phase 3 follow-up issue (linked below).

> **Read [`../README.md`](../README.md) first.** It locks sensitivity classification, persona vocabulary, pinned references, and the skip-reason taxonomy used here.

---

## How to read this catalog

Every captured (route, persona) pair has three files in the persona's directory:

| File | Purpose |
|------|---------|
| `<NNN>-<route>.desktop.webp` | Full-page screenshot at 1440×900 |
| `<NNN>-<route>.mobile.webp` | Full-page screenshot at 390×844 |
| `<NNN>-<route>.md` | Caption — frontmatter + (Phase 3) observed CTAs + interaction notes |

Numbering is 3-digit zero-padded, sequential within the persona section. The caption's `lead_viewport` field encodes which viewport is canonical for the persona: Caregiver and Family Member lead with **mobile** (per [`docs/design-system/RESPONSIVE.md`](../../design-system/RESPONSIVE.md) — they operate from phones in the field); other personas lead with desktop. Both viewports are always captured.

The caption is the cross-reference handle. Its frontmatter `canonical_id` field (e.g., `agency-admin/001-todays-shifts`) is what the [pages inventory](../../migration/v1-pages-inventory.md) `screenshot_ref` column points at.

## Caption schema

```yaml
---
canonical_id: <persona-slug>/<NNN>-<route-slug>
route: <v1 URL pattern, with <int:id> placeholders>
persona: <canonical persona name from ../migration/README.md>
lead_viewport: desktop | mobile
seed_state: populated | empty
v1_commit: <SHA the catalog was generated against>
generated: <YYYY-MM-DD>
---
**CTAs visible:** <comma-separated list of buttons/links observable in the screenshot>

**Interaction notes** (1–4 bullets, observed behavior only):
- <element> → <result>
- ⚠ destructive: <element> → <result>. Skipped by crawler.
```

Interaction-note rules (from [#79](https://github.com/suniljames/COREcare-v2/issues/79) Writer review): observed behavior only, no speculation, format `<element> → <result>`. Destructive interactions get a `⚠ destructive:` prefix and **must not** be triggered by the crawler.

## Persona index

Persona section order matches [`../../migration/README.md` §Personas](../../migration/README.md#personas). Within-persona routes are ordered by `canonical_id` ascending (sequence number preserves "what comes next" navigation).

| Persona | Directory | Captures | Lead viewport |
|---------|-----------|---------:|---------------|
| Super-Admin | [`super-admin/`](super-admin/) | 1 | desktop |
| Agency Admin | [`agency-admin/`](agency-admin/) | 61 | desktop |
| Care Manager | [`care-manager/`](care-manager/) | 3 | desktop |
| Caregiver | [`caregiver/`](caregiver/) | 15 | **mobile** |
| Client | [`client/`](client/) | 0 (no v1 portal) | n/a |
| Family Member | [`family-member/`](family-member/) | 4 | **mobile** |

**Total:** 84 captured (route, persona) pairs × 2 viewports = 168 WebP files via Git LFS. 50 inventory rows are recorded as `not_screenshotted: <reason>` in [`docs/migration/v1-pages-inventory.md`](../../migration/v1-pages-inventory.md) per the [skip-reason taxonomy](../README.md#skip-reason-taxonomy).

The Client persona has no captures because v1 has no Client login portal — Client is an object-of-care, not a User. See [`tools/v1-screenshot-catalog/INVESTIGATIONS.md`](../../../tools/v1-screenshot-catalog/INVESTIGATIONS.md#persona-authentication-mapping) for the persona-mapping decisions.

## Coverage

Run [`../../../scripts/check-v1-catalog-coverage.sh`](../../../scripts/check-v1-catalog-coverage.sh) to verify that every inventory row either has a matching caption file or carries a `not_screenshotted: <reason>` skip-reason. The CI workflow [`v1-catalog-coverage.yml`](../../../.github/workflows/v1-catalog-coverage.yml) runs this check automatically on PRs touching the inventory or this catalog. Current state: **100% coverage, 0 orphans.**

## Generation provenance

This catalog was generated on **2026-05-07** by running the [`tools/v1-screenshot-catalog/`](../../../tools/v1-screenshot-catalog/) crawler against v1 at commit [`9738412a`](https://github.com/hcunanan79/COREcare-access/commit/9738412a6e41064203fc253d9dd2a5c6a9c2e231) with a PHI-scrubbed seed fixture (sha256 [`03b41480…3afdf92`](../../../tools/v1-screenshot-catalog/INVESTIGATIONS.md#fixture-snapshot)). Authoritative crawl ran for ~62 seconds; reproducibility re-run + pixelmatch diff confirmed 166/168 images within the 0.5%-pixel-diff threshold (2 marginal outliers documented in [`reproducibility-report/report.md`](reproducibility-report/report.md)).

The full audit trail — pre-flight gates, network-interception log, PHI placeholder vocabulary used by the fixture, RUN-DATE, route counts — lives in [`RUN-MANIFEST.md`](RUN-MANIFEST.md) alongside the screenshots. Caption bodies (CTAs visible + interaction notes per [`tools/v1-screenshot-catalog/CAPTION-STYLE.md`](../../../tools/v1-screenshot-catalog/CAPTION-STYLE.md)) are tracked in the Phase 3 caption-authoring follow-up issue and land in a follow-up PR.

### Refresh

When v1 advances and the catalog needs a refresh, follow [`tools/v1-screenshot-catalog/PHASE-2-RUNBOOK.md`](../../../tools/v1-screenshot-catalog/PHASE-2-RUNBOOK.md). The runbook documents the v1 bring-up sequence, fixture re-validation, crawler invocation, reproducibility two-run, and PR procedure.
