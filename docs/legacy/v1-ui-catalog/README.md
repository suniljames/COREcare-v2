# v1 UI Catalog — Index

**Status:** SCAFFOLDED. Catalog binaries (WebP screenshots) and captions land in [#107](https://github.com/suniljames/COREcare-v2/issues/107). Until then: this index lists the persona directory structure and the conventions captions will follow.

> **Read [`../README.md`](../README.md) first.** It locks sensitivity classification, persona vocabulary, pinned references, and the skip-reason taxonomy used here.

---

## How to read this catalog

Every captured (route, persona) pair has three files in the persona's directory:

| File | Purpose |
|------|---------|
| `<NNN>-<route>.desktop.webp` | Full-page screenshot at 1440×900 |
| `<NNN>-<route>.mobile.webp` | Full-page screenshot at 390×844 |
| `<NNN>-<route>.md` | Caption — frontmatter + observed CTAs + interaction notes |

Numbering is 3-digit zero-padded, sequential within the persona section. Caregiver- and Family-Member-mobile-primary surfaces still produce both viewports; the caption lists `viewport: mobile` as the lead — see [`../README.md`](../README.md).

The caption is the cross-reference handle. Its frontmatter `canonical_id` field (e.g., `agency-admin/001-dashboard`) is what the [pages inventory](../../migration/v1-pages-inventory.md) `screenshot_ref` column points at.

## Caption schema

```yaml
---
canonical_id: <persona-slug>/<NNN>-<route-slug>
route: <v1 URL pattern, with `:id` placeholders>
persona: <canonical persona name from ../migration/README.md>
viewport: desktop | mobile
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

| Persona | Directory | Status |
|---------|-----------|--------|
| Super-Admin | [`super-admin/`](super-admin/) | Scaffolded — pending #107 |
| Agency Admin | [`agency-admin/`](agency-admin/) | Scaffolded — pending #107 |
| Care Manager | [`care-manager/`](care-manager/) | Scaffolded — pending #107 |
| Caregiver | [`caregiver/`](caregiver/) | Scaffolded — pending #107 |
| Client | [`client/`](client/) | Scaffolded — pending #107 (depends on v1 client-portal seeding) |
| Family Member | [`family-member/`](family-member/) | Scaffolded — pending #107 |

Each persona directory will be populated by the crawler in #107. Per-persona route lists are derived from the [pages inventory](../../migration/v1-pages-inventory.md) — that is the authoritative source.

## Coverage

Run [`../../../scripts/check-v1-catalog-coverage.sh`](../../../scripts/check-v1-catalog-coverage.sh) to verify that every inventory row either has a matching caption file or carries a `not_screenshotted: <reason>` skip-reason. The CI workflow [`v1-catalog-coverage.yml`](../../../.github/workflows/v1-catalog-coverage.yml) runs this check automatically on PRs touching the inventory or this catalog.

## Generation provenance

Once #107 lands, this section will hold:

- v1 commit SHA the catalog was generated against
- Seed-data snapshot hash
- Generation timestamp
- Crawler version (link to `hcunanan79/COREcare-access` PR)
- `RUN-MANIFEST.md` link (audit trail of routes visited / skipped / errored)
