# Caption Authoring Style Guide

> Read [`INVESTIGATIONS.md`](INVESTIGATIONS.md) and [`PHI-CHECKLIST.md`](PHI-CHECKLIST.md) first.

This guide governs the body of every caption file in [`docs/legacy/v1-ui-catalog/`](../../docs/legacy/v1-ui-catalog/). Caption frontmatter (`canonical_id`, `route`, `persona`, `viewport`, `seed_state`, `v1_commit`, `generated`) is written mechanically by the crawler. The body — `**CTAs visible:**` and `**Interaction notes**` — is **author-written by a human** in [#107](https://github.com/suniljames/COREcare-v2/issues/107) Phase 3, the follow-up authoring pass.

The crawler initially writes `<!-- TODO: author CTAs + interaction notes -->` placeholders. Each caption gets ~5 minutes of authoring; for ~300 routes, expect ~25 hours of work for one pass.

---

## Voice

- **Present tense, declarative, third-person observational.** "The page shows a list of clients." Not "You can see clients here."
- **Specificity over abstraction.** Name the visible element, not its function. "The 'Approve' button" not "the approve action." "The blue alert banner" not "an indicator."
- **No second person.** Never "you," "your." The catalog reader is a generic future v2 contributor, not the user of v1.
- **No first person.** Never "we," "our," "us," "I."
- **No speculation about user intent.** Describe what's on the screen, not what the user is trying to accomplish.
- **No speculative qualifiers.** Forbidden: "probably," "likely," "might," "may," "seems," "appears to."
- **No editorial commentary.** Don't say "this is confusing" or "this looks dated" — the catalog is a reference, not a critique.
- **No conditional/spec language.** Forbidden: "should be," "could be," "would be," "ought to." The catalog describes what v1 IS, not what v2 should do.
- **Behavior is described against the captioned `seed_state`.** Do not describe alternative states ("if the list were empty…"). The frontmatter `seed_state` field captures which state was observed. If a caption needs another state, that's a re-crawl + split — out of scope for the Phase 3 authoring pass (#184).

---

## CTAs visible

- One inline list, comma-separated, prefixed `**CTAs visible:**`.
- Maximum 10 items. If more buttons / links are visible, keep the 10 most prominent (visual hierarchy).
- Use the literal label as displayed. Wrap in double quotes: `"Approve Timesheets"`, not `Approve Timesheets button`.
- For unlabeled icon buttons, describe the icon: `"calendar icon (top-right header)"`.
- Order matches the visual reading order on the page (top-to-bottom, left-to-right at desktop).
- If the page has no CTAs (e.g., a read-only detail view): `**CTAs visible:** none — read-only view.`

---

## Interaction notes

- 1–4 bullets, no more. If a page has more than 4 distinct interactions worth documenting, the caption probably wants splitting (see "Splitting captions" below).
- **Format:** `<element> → <result>`. Element first, result after a `→` arrow.
- **Element** names exactly as displayed. **Result** describes what the page does when the element is interacted with — observed behavior only, not speculation.
- For destructive interactions (POST/DELETE that mutates data): prefix with `⚠ destructive:` and document that the crawler skipped the interaction. Authors must NOT click destructive interactions (it mutates the seed DB, breaking later sessions). Describe by reading v1 source (`urls.py` + view function), not by clicking.
- If the result navigates to another page in the catalog, link the canonical_id: `→ navigates to [agency-admin/015-shift-detail](../agency-admin/015-shift-detail.md)`. **Link text MUST equal the target's canonical_id** (e.g., `agency-admin/015-shift-detail`), not arbitrary prose like `Shift Detail` or `here`. Cross-references are checked by `scripts/check-v1-caption-voice.sh`.
- If the interaction triggers something not visible (a background API call, an email send), note it without speculation about side effects. **HTTP paths in interaction notes must be verified against v1 source** (`urls.py` + view function) or omitted in favor of an observational result. "→ POSTs to `/timesheets/<id>/approve/`" — yes, if confirmed by reading v1 source; "→ POSTs to `/timesheets/<id>/approve/`, sends notification email to client" — only if the catalog author confirmed both legs by reading v1 source.

---

## PHI references in captions

- **Never name a placeholder value in a caption.** Forbidden: `"Shows John Doe's chart"` or `"Shows [CLIENT_NAME]'s chart"`. Even though `[CLIENT_NAME]` is locked placeholder text, repeating it in the caption noise-floors the search index and reduces caption usefulness when the placeholder set evolves.
- **Use the role:** `"Shows the assigned client's chart"`, `"Lists the caregivers who reported expenses this week"`. Captions describe what the page shows in terms of the data structure, not the (placeholder) data values.
- If a caption needs to reference a specific data state (empty / populated / archived), use the `seed_state` frontmatter field rather than restating it in the body.

---

## Length

- Caption files, end-to-end, fit on a single screen. Target ≤300 words of body content.
- If a caption is growing past 300 words, the page probably has multiple distinct UI states worth splitting (modal-vs-no-modal, expanded-vs-collapsed, populated-vs-empty). Split.

---

## Splitting captions

If a route has multiple distinct visual states, generate one caption per state with sub-letter suffixes:

- `015a-shifts-list.md` (default state)
- `015b-shifts-list-with-filters-applied.md` (filters open)
- `015c-shifts-list-empty-state.md` (no shifts)

The numeric prefix stays the same (route-level identity); the letter disambiguates the state. The frontmatter `seed_state` field captures which state each variant represents.

**Splitting is out of scope for Phase 3 authoring (#184).** Splits require re-capturing screenshots for each new sub-state — that's a re-crawl, not an authoring task. If you find a caption that genuinely needs splitting during the Phase 3 pass, file a follow-up issue and proceed with a single best-effort caption against the captured state.

---

## Two example captions

### Good — `agency-admin/015-shifts-list.md`

```markdown
---
canonical_id: agency-admin/015-shifts-list
route: /admin/todays-shifts/
persona: Agency Admin
viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-07
---
**CTAs visible:** "Filter", "Export CSV", "+ New Shift", row-level "Edit" links, row-level "Cancel" links.

**Interaction notes:**
- "Filter" button → opens a panel with date range, caregiver, and client filters.
- "Export CSV" button → downloads the current filtered list as CSV.
- Row-level "Edit" link → navigates to [agency-admin/016-shift-detail](016-shift-detail.md).
- ⚠ destructive: row-level "Cancel" link → POSTs to `/admin/shifts/<id>/cancel/`. Skipped by crawler.
```

**Why this works:**
- Frontmatter is mechanical (the crawler wrote it).
- CTA list uses literal labels, in reading order, wrapped in double quotes.
- Interaction notes are 4 bullets, format `<element> → <result>`, observed behavior only.
- Cross-reference to another caption uses the canonical_id link.
- Destructive interaction is `⚠ destructive:` prefixed and noted as crawler-skipped.
- No speculation, no editorial commentary, no "you" voice.

### Anti-pattern — what NOT to write

```markdown
---
canonical_id: agency-admin/015-shifts-list
route: /admin/todays-shifts/
persona: Agency Admin
viewport: desktop
---
**CTAs visible:** Filter, Export, New Shift, Edit, Cancel, Sort By Date, Sort By Caregiver, Refresh, Settings, Help, Search, Group By Status

**Interaction notes:**
- You'll probably want to use the Filter button first to narrow down the list before exporting. The export feature is a bit slow because it loads everything into memory before generating the CSV — this is a weak point that v2 should improve. The interface here is from v1 which is showing its age. A specific named person would click "Edit" to update her client's shift, but I'm not sure if the page actually saves correctly because I had a bug last week.
```

**What's wrong:**
- Frontmatter missing required `seed_state`, `v1_commit`, `generated` fields.
- 12 CTAs listed (over the 10 cap), without quote-wrapping, without reading-order discipline.
- "You'll probably want to" — second person, speculation about user intent.
- "weak point that v2 should improve" — editorial commentary; the catalog is a reference, not a v2 spec.
- "A specific named person" stand-in (in the original anti-pattern, an actual first-last name) — naming any person, placeholder or otherwise, violates the PHI-references rule.
- "I'm not sure if the page actually saves correctly" — uncertainty in observed behavior; either confirm the behavior by testing or omit the bullet.
- Single prose paragraph instead of `<element> → <result>` bullets.

---

## Authoring workflow

### Step 0 — Per-session preconditions

Before opening any caption file:

1. `cd ~/Code/COREcare-access && git fetch && git checkout 9738412a6e41064203fc253d9dd2a5c6a9c2e231`.
2. `unset DATABASE_URL` (default SQLite per [INVESTIGATIONS.md](INVESTIGATIONS.md)).
3. `python manage.py migrate` against a **fresh** SQLite DB (delete the SQLite file from any prior session — destructive interactions during prior sessions could have mutated state).
4. `python manage.py loaddata fixtures/v2_catalog_snapshot.json`.
5. From the v2 worktree: `bash scripts/v1-author-precheck.sh` — must exit 0 (asserts the operator's local fixture sha256 matches `RUN-MANIFEST.md`). If it fails: STOP and re-load the fixture.
6. `python manage.py runserver 0.0.0.0:8000`.
7. Append a session entry to [`AUTHORING-LOG.md`](AUTHORING-LOG.md): timestamp + persona section.

### Per-caption workflow

1. `grep -rl '<!-- TODO: author CTAs' docs/legacy/v1-ui-catalog/<persona-slug>/` to find the next unfinished caption.
2. **Open the caption's lead-viewport image** as the reading-order reference: `<NNN>-<slug>.desktop.webp` for desktop-lead personas (Super-Admin, Agency Admin, Care Manager); `<NNN>-<slug>.mobile.webp` for mobile-lead personas (Caregiver, Family Member). The lead viewport is locked in the caption's `lead_viewport` frontmatter field.
3. Open the route in v1 logged in as the matching persona.
4. List visible CTAs in reading order (top-to-bottom, left-to-right at the lead viewport). Trim to the 10 most prominent. Quote-wrap each label. Use position descriptors for unlabeled icons: `"calendar icon (top-right header)"`.
5. Identify 1–4 worth-documenting interactions. For each:
   - Click non-destructive interactions; describe the result observationally.
   - For destructive interactions (POST/DELETE that mutates data): **do not click**. Describe by reading v1 source (`urls.py` + view function). Prefix bullet with `⚠ destructive:` and note "Skipped by crawler."
6. Format each interaction note as `<element> → <result>`. If the result navigates within the catalog, link by canonical_id (link text MUST equal the canonical_id).
7. **HTTP paths in interaction notes must be verified against v1 source** (`urls.py` + view function), or omitted in favor of an observational result.
8. Replace the `<!-- TODO: author CTAs + interaction notes -->` placeholder with `**CTAs visible:** ...\n\n**Interaction notes:**\n- ...` body.
9. **Do not modify frontmatter.** Authors edit only the body (everything after the trailing `---`). Frontmatter immutability is enforced by pre-commit + CI.
10. Confirm caption file size <1 KB.
11. `git add` + commit (the pre-commit hook runs hygiene + voice + body-PHI lints over the staged caption).

### Locked decisions for Phase 3 (#184)

- **No splits, no re-captures, no new captions** — only body content for the existing 84 files. Discovered split candidates are filed as follow-ups.
- **Frontmatter is immutable** — authors edit only the body.
- **Cross-reference link text is the canonical_id** (e.g., `[agency-admin/015-shifts-list](015-shifts-list.md)`).
- **Interaction notes use `<element> → <result>` bullets — no prose paragraphs.**
- **Behavior is described against the captioned `seed_state`** (currently `populated` for all 84 captures). No alt-state speculation.
- **HTTP paths verified or omitted** — no path speculation.

### After authoring all 84 captions

- Run `bash scripts/check-v1-catalog-coverage.sh` — confirms parity with the inventory.
- Run `bash scripts/check-v1-captions-authored.sh` — asserts no `<!-- TODO -->` markers remain (or `make test-v1-captions-authored`).
- Run `bash scripts/check-v1-doc-hygiene.sh docs/legacy/v1-ui-catalog/**/*.md` — PHI / real-name / abs-path scan.
- Run `bash scripts/check-v1-caption-phi.sh docs/legacy/v1-ui-catalog/**/*.md` — body-scoped placeholder forbid.
- Run `bash scripts/check-v1-caption-voice.sh docs/legacy/v1-ui-catalog/**/*.md` — voice + format + cross-ref lint.
- Run the cold smoke test ([T7-COLD-SMOKE-TASKS.md](T7-COLD-SMOKE-TASKS.md)): two v2 contributors without v1 access, three sealed-envelope tasks, `<60s` each. 6/6 = pass.
- Commit `PHI-AUDIT-POSTAUTHORING-<YYYY-MM-DD>.md` with the 11-category checklist over a sample (1/persona for small + 5 random for agency-admin).
