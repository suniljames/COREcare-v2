# V1 Reference Documentation Set

This directory holds reference material about COREcare **v1** (`suniljames/COREcare-access`, a Django monolith) for collaborators building **v2** without v1 source access. The docs describe what v1 does so v2's ground-up rebuild does not silently drop customer-facing capability.

**Audience:** engineers contributing to v2, including AI agents acting on their behalf. **Not customer-facing.**

**Sensitivity:** internal. No PHI, no real customer data, no production identifiers. See [PHI Placeholder Convention](#phi-placeholder-convention).

**Owner:** [Sunil James](https://github.com/suniljames) (`@suniljames`) — single named owner for the docset's accuracy and refresh cadence.

---

## V1 Reference Commit

All facts in this docset were reconciled against:

- **Repo:** `suniljames/COREcare-access`
- **Commit SHA:** `9738412a6e41064203fc253d9dd2a5c6a9c2e231`
- **Commit subject:** `feat(#1479): January annual mileage-rate verification banner (#1480)`
- **Pinned at:** 2026-05-06

Authors of follow-up content updates: capture v1 `HEAD` at start of authoring (`git -C <v1-checkout-path> rev-parse HEAD`) and update this section. **Do not chase v1 advances mid-authoring** — finish against the pinned SHA, then file a refresh issue.

---

## Document set

```
docs/migration/
├── README.md                           # this file — conventions, owner, runbook
├── v1-glossary.md                      # v1-specific terms (View As, magic link, BillableServiceCatalog, etc.)
├── v1-pages-inventory.md               # persona × page matrix (the spine — other docs cite into it)
├── v1-user-journeys.md                 # narrated end-to-end flows per persona
├── v1-integrations-and-exports.md      # external integrations + internal notification/email + customer-facing exports
├── v1-functionality-delta.md           # feature/data-model gaps with severity (existing)
└── CUTOVER_PLAN.md                     # migration cutover plan (existing, separate scope)
```

**Dependency direction** (no cycles):

```
v1-pages-inventory.md  ── spine
        ▲    ▲    ▲
        │    │    └── v1-user-journeys.md      (cites inventory anchors)
        │    └─────── v1-integrations-and-exports.md (cites inventory anchors where integrations surface in UI)
        └──────────── #79 (Playwright screenshot catalog, separate issue, depends on inventory for coverage)

v1-functionality-delta.md  ── feature/data-model layer
        cross-refs into the above via top-of-file collaborator header

v1-glossary.md  ── terms cited across all docs
```

The pages inventory is the authoritative route catalog. Other docs do not redefine routes; they link to inventory rows.

---

## Locked conventions

These conventions apply to every document in this set. **Authors must read this section before writing or editing.**

### Personas

Six personas, exact strings from `.claude/pm-context.md`:

- `Super-Admin`
- `Agency Admin`
- `Care Manager`
- `Caregiver`
- `Client`
- `Family Member`

No drift to lowercase, no hyphenation changes, no synonyms ("admin," "agency administrator," "care worker," "field worker").

### v2 status enum

Exactly three values:

- `implemented` — equivalent v2 surface exists and is wired
- `scaffolded` — v2 model/router exists but isn't reachable from the UI
- `missing` — no v2 equivalent exists

No "in progress," no "partial," no "planned." If finer granularity is needed, expand this enum explicitly via a new PR.

### Severity rubric

Inherited from `v1-functionality-delta.md`. Apply only when `v2_status = missing`.

| Code | Meaning |
|------|---------|
| `H` | High — must-fix for v1.0 GA parity |
| `M` | Medium — should-fix |
| `L` | Low — nice-to-have |
| `D` | Deliberate — intentional v2 divergence (gain or removal) |

### Visual markers

Pair an emoji with the text fallback so screen readers and grep both work:

- `🔴 H · missing`
- `🟡 M · scaffolded`
- `🟢 implemented`
- `⚪ D · deliberate divergence`

### PHI Placeholder Convention

**v1 contains real PHI. No PHI in committed docs. Use only the following placeholders:**

```
[CLIENT_NAME]      [CAREGIVER_NAME]    [AGENCY_NAME]
[CLIENT_DOB]       [CLIENT_MRN]        [DIAGNOSIS]
[MEDICATION]       [NOTE_TEXT]
[ADDRESS]          [PHONE]             [EMAIL]
[SHIFT_ID]         [VISIT_ID]          [INVOICE_ID]
[REDACTED]
```

All-caps in brackets. **Never use plausible-looking fake names** like `Jane Doe` or `Sarah Johnson` — placeholders only. The hygiene scanner blocks the most common PHI patterns; the placeholder set lets it distinguish intentional placeholders from suspicious content.

If a v1 page renders specific structured data, describe the structure without examples: "client name, DOB, current medications list" — not specific values.

### Voice and tense

- **Present tense for v1.** v1 is running today: "v1 displays...", not "v1 displayed...".
- **Active voice.** "v1 sends an email when..." not "an email is sent when...".
- **Third-person, structural prose** for inventory and journey content.
- **Second-person reserved** for top-of-file lead paragraphs orienting the reader.
- **No first-person "I."** No unscoped "we" in declarative content (`v1 supports magic links`, not `we support magic links`).

### Quoted v1 UI strings

When citing literal v1 UI text (button labels, help text, error messages, notification templates), enclose in a blockquote with attribution:

```markdown
> v1 displays: "Are you sure you want to void this invoice? This cannot be undone."
```

Plain prose is the doc author's voice. Blockquotes are direct v1 strings. **Never inline v1 imperative text as prose** — an AI agent reading the doc must be able to distinguish description from instruction.

### V1 source references

Refer to v1 by GitHub repo slug `suniljames/COREcare-access`. **Never by absolute filesystem path** (`/Users/`, `/home/`, drive letter). The hygiene scanner blocks absolute paths.

When citing a specific v1 file, use the form `<app>/<file>:<line>` — for example, `billing/views.py:142`. The repo slug is implied by context.

### Cross-references

Linked text is descriptive: write **the Agency Admin pages section** of the v1 pages inventory, not `see #v1-pages-inventory.md`. The reader must know where they're going before they click.

Anchors must be stable. Define section anchors with `<a id="..."></a>` immediately under the heading if the markdown flavor's auto-anchor would be unstable across heading edits.

### Section-level metadata

Every persona section in `v1-pages-inventory.md` carries a single line under its H2:

```markdown
## Agency Admin

_last reconciled: 2026-05-06 against v1 commit `9738412`_
```

Update on each refresh.

### Row prose conventions

These conventions apply inside every persona section in `v1-pages-inventory.md`. Locked in #81 to keep the five subsequent persona-section PRs from drifting.

**H3 sub-headings group rows by Django app.** Within a persona section, group rows under one H3 per Django app the persona reaches. Heading text is lowercase, matching v1's Django app directory verbatim. Each H3 carries a one-line purpose summary directly under it.

```markdown
### billing
_invoices, payment tracking, payer reconciliation_

| route | purpose | … |
```

Row order within an app group: typical workflow progression (index → list → detail → action), not alphabetical.

**`purpose` cell is a sentence (80–120 chars), not a label.** Use simple present-tense, third-person verbs. `Lists open and overdue invoices, with filters by client and date range.` beats `Invoice list page`. Avoid `allows the user to`, `enables`, `manages` — substitute concrete verbs (`displays`, `lists`, `accepts`, `submits`, `triggers`).

**`what_user_sees_can_do` cell follows the `Sees: <list>. Can: <list>.` pattern.**

```
Sees: open and overdue invoices, payer and date filters. Can: drill to invoice detail, void invoice, mark paid.
```

Comma-separated lists. Sentences end with a period. The pattern is structural, scannable, and agent-parseable — drift to other phrasings breaks downstream queries.

**Verbatim flag-column tokens.** Cells in flag columns contain exactly the schema-locked token, lowercase, no surrounding text:

- `v2_status` cell: exactly `implemented` / `scaffolded` / `missing`.
- `severity` cell: exactly `H` / `M` / `L` / `D` or empty.
- `multi_tenant_refactor` cell: exactly `true` or `false`.
- `phi_displayed` cell: exactly `true` or `false`.
- `rls_bypass_by_design` cell: exactly `true` or `false`.

`yes` / `True` / `partial` / `WIP` are bugs, not synonyms.

**PHI flag prominence.** When `phi_displayed=true`, prefix the row's `purpose` cell with `🔒 PHI · ` so PHI surfaces are scannable in a wide table:

```
🔒 PHI · Lists assigned clients with caregiver matching status.
```

The textual `PHI` is the screen-reader fallback.

**Multi-tenant refactor justification.** `multi_tenant_refactor=false` requires an explicit justification phrase in the same row's `purpose` cell (e.g., `v2 equivalent already RLS-isolated; no further refactor needed`). Default is `true`; v1 was single-tenant per install so most v2 equivalents need new tenant-context awareness.

**RLS-bypass audit notes.** Every `rls_bypass_by_design=true` row's `purpose` cell notes v1 audit-log behavior: `audit-logged in v1` (preserve in v2 design) or `v1 has no audit on this route — v2 must add` (compliance gap to fix on rebuild).

**Anchor stability.** H3 sub-headings carry stable anchors (lowercase app name) so cross-references from `v1-user-journeys.md`, `v1-integrations-and-exports.md`, and the screenshot catalog (#79) resolve. Do not rename `### billing` to `### Billing` or `### Billing & Revenue` between PRs.

---

## Coverage target

The pages inventory targets ≥95% coverage of distinct v1 URL patterns (function-based or class-based views serving HTML).

**Counted (denominator):**
- All FBVs and CBVs serving HTML, in `urls.py` files (root + per-app).
- Flag-toggled views regardless of feature-flag state.

**Not counted:**
- Django admin auto-generated routes (`/admin/<model>/`).
- JSON-only API endpoints (no HTML render).
- Redirect-only views (`RedirectView`).
- Static-asset routes.

**Numerator:** number of (URL pattern) entries covered by at least one row in `v1-pages-inventory.md`.

The current denominator and numerator are recorded in `v1-pages-inventory.md` under a "Coverage" section near the top of the file.

---

## Hygiene and structure enforcement

Two scripts validate this docset on every PR:

- `scripts/check-v1-doc-hygiene.sh` — blocks PHI patterns, absolute paths, plausible-real-name two-word sequences. Run via pre-commit hook and CI.
- `scripts/check-v1-doc-structure.sh` — validates persona-section coverage in pages inventory and the cross-reference header in the delta doc.

Self-tests:

```sh
make test-v1-docs    # run the script self-tests
make scan-v1-docs    # run the scripts over the actual committed docs
```

CI workflow: `.github/workflows/v1-doc-hygiene.yml`. Runs on PRs that touch `docs/migration/v1-*.md` or the scripts.

Pre-commit hook: `.pre-commit-config.yaml`. Install once with `pip install pre-commit && pre-commit install`.

---

## Refresh runbook

When v1 receives material changes, refresh this docset against the new SHA.

1. Pull v1 to a local checkout. Capture `git -C <v1> rev-parse HEAD` — the new pin.
2. Diff against the previously-pinned SHA in this README. Identify changed apps.
3. For each changed app, read `urls.py`, views, and templates. Update the pages-inventory rows for affected routes; update journeys if a flow changed end-to-end; update integrations doc if external service contracts changed.
4. Bump `last reconciled` dates in updated persona sections. Update the SHA in this README.
5. Run `make scan-v1-docs` locally. Open a PR titled `docs(migration): refresh v1 reference set against <short-sha>`.

If you find yourself doing this more than twice manually, automate it (per the team's "if you do it twice" principle). The first automation candidate is the `urls.py` enumeration step.

### Family Member section — extra diff checks before re-authoring

Family Member is the lowest-frequency persona for v2 development AND the lowest-frequency persona surface in v1. Small family-portal patches accumulate undetected between refreshes — silent drift the hygiene scanner cannot catch. Run these checks every time the `V1 Reference Commit` above is bumped, regardless of which persona motivated the bump.

In your local v1 checkout, against the previously-pinned SHA:

- `git diff <old>..<new> -- '*/urls.py'` — surfaces new family-prefixed routes anywhere in v1, including sub-URLConf refactors a top-level `dashboard/urls.py` diff would miss.
- `git diff <old>..<new> -- clients/` — surfaces changes to permission gating, serializers, and family-facing templates. Helper names like `_check_client_access`, body checks like `is_family or …`, and template tags like `{% if is_family %}` are *examples of what to look for*, not a fixed contract — the gate may be renamed but the semantics are what matter.
- `git diff <old>..<new> -- clients/models.py` — surfaces `ClientFamilyMember` schema shifts.

Baseline at the currently-pinned SHA: `ClientFamilyMember` has no `is_active`, no soft-delete, no expiry, and no role/permission column — any of those appearing in the diff is a behavioral change that propagates into the section's rows.

If any diff is non-empty: re-author affected rows in `v1-pages-inventory.md`. If `_check_client_access` or any family-permission gate changed: also flag `CUTOVER_PLAN.md` owners — v2 RLS may need to mirror the v1 change. If all diffs are empty: still bump `last reconciled` on the Family Member section. An empty diff is signal; the reconciliation date is the artifact.

**Refresh order — Agency Admin first.** Agency Admin is the most-iterated persona surface in v1 (billing, payroll, scheduling, credentials, compliance). When budget for a refresh is constrained, refresh Agency Admin first; file follow-ups for other personas. The pattern Agency Admin establishes (cell prose, H3 naming, flag accuracy) is the template subsequent persona refreshes inherit.

---

## Workflow secrets

CI workflows that touch the private v1 repo (`suniljames/COREcare-access`) authenticate via repo-level secrets. Maintainer-managed; engineers do not need to action these unless adding a new workflow or rotating an existing token.

### `V1_REPO_READ_TOKEN`

Used by `.github/workflows/v1-sha-bump-diff-report.yml` (#131) to clone v1 and run the three Family Member runbook diffs (per the runbook entry above) when a PR bumps the V1 Reference Commit SHA.

- **Type:** GitHub fine-grained personal access token.
- **Repository access:** `suniljames/COREcare-access` only — never wildcard.
- **Repository permissions:** `Contents: Read`. Nothing else.
- **Expiration:** 1 year. Calendar a rotation reminder when issuing.
- **Last rotated:** 2026-05-07 (initial issuance).
- **Stored at:** repo Actions secrets, name `V1_REPO_READ_TOKEN`.

**Rotation procedure.** Re-issue the PAT with the same scope and expiry, update the `V1_REPO_READ_TOKEN` secret in the v2 repo settings, then bump the **Last rotated** date above in the PR that records the rotation.

**Break-glass.** If the diff-report gate is broken (PAT expired, v1 unreachable, comment-API failure) and a refresh PR is in flight: the engineer runs the three diffs locally per the [Family Member section runbook entry](#family-member-section--extra-diff-checks-before-re-authoring) above, documents the result in the PR description, and a maintainer uses branch-protection bypass to merge. Then file a new issue to fix the gate. Do not silence the gate; fix it.

---

## Related work

- **#70 (closed)** — landed `v1-functionality-delta.md` (the feature/data-model layer this set extends).
- **#78** — umbrella issue for v1 reference content authoring; tracks all persona-section sub-issues.
- **#80 (closed)** — landed conventions, scanner, structure validator, scaffold.
- **#81** — Agency Admin pages-inventory rows; first persona-section content-authoring PR; locked the row-prose conventions above.
- **#79 (open, follow-up)** — Playwright screenshot catalog of v1 UI per persona; depends on populated rows for coverage check.
- **#31, #32 (closed)** — v1→v2 data migration scripts and cutover plan.
