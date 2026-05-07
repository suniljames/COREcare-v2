# V1 Glossary

> **Read [`README.md`](README.md) first.** It locks the persona vocabulary.

Terms specific to COREcare v1 (`suniljames/COREcare-access`) that appear across this docset. **Persona names** (`Super-Admin`, `Agency Admin`, `Care Manager`, `Caregiver`, `Client`, `Family Member`) and general homecare vocabulary (`Care Plan`, `Visit`, `Shift`, `ADLs`, `PHI`) are defined in [`.claude/pm-context.md`](../../.claude/pm-context.md), not duplicated here.

This file extends `pm-context.md` with v1-specific terms — model names, internal feature names, and Django app names that come up when reading v1 source.

**Status:** SCAFFOLDED. Entries are pending authoring against the [pinned v1 commit](README.md#v1-reference-commit). The set below is seeded from terms already cited in `v1-functionality-delta.md`.

---

## Format

For each term: one-line definition, then a link to its first significant use in this docset (a heading anchor in `v1-pages-inventory.md`, `v1-user-journeys.md`, or `v1-integrations-and-exports.md`).

---

## Pending entries

Terms that need definition before the docset is complete:

- **`elitecare`** — the Django project root for v1; not an app name. Cited in `v1-functionality-delta.md` and any model-namespacing references.
- **`InvoiceRevision`** — v1 model representing a corrected, reissued invoice. (`H`-severity gap in delta.)
- **`BillableServiceCatalog`** — v1 model for agency-managed billable add-on services. (`H`-severity gap in delta.)
- **`ChartTemplate`** — v1 model for per-client chart customization. (`H`-severity gap in delta.)
- **`MagicLinkToken`** — v1 model backing email-based magic-link login.
- **View-As impersonation** — v1 super-admin feature for assuming an agency-admin context with full audit trail. (`H`-severity gap; load-bearing compliance control.)
- **`promote_to_recurring_view()`** — v1 view function cited in delta; converts a one-off scheduling decision into a recurring rule.
- **`issue_revision_editor()`** — v1 view function for the corrected-invoice editor flow.
- **Profile completion gate** — v1 onboarding control that blocks caregivers from accepting shifts until required profile fields are filled.
- **9-category expense workflow** — v1 expense submission with nine fixed expense classes. (`M`-severity gap.)
- **Meal-break waiver** — v1 caregiver-consent record for waiving meal breaks under state labor rules.
- **Overpayment consent** — v1 acknowledgment record for caregivers to accept an overpayment correction.
- **Action queue** — v1 deterministic-detection feed of items needing a coordinator response, distinct from v2's planned AI-driven coordination assistant.
- **Health report approval queue** — v1 dual-author health report flow with an explicit approval gate.
- **`ClientFamilyMember`** — v1 model linking a Django `User` to a `Client` for family-portal visibility; carries per-link permission booleans (`can_view_schedule`, `can_message_caregivers`) and `unique_together(client, user)` but no soft-delete or active flag — revocation is hard-delete in v1. Cited in [`## Family Member`](v1-pages-inventory.md#family-member) section lead and in cross-reference index entries for `clients/` calendar/event routes.

_(definitions pending content authoring; each will resolve to one-line text + first-use link)_

---

## Cross-cutting v1 conventions

These are not single terms but recurring patterns in v1 source. Calling them out here because they show up in inventory rows and journey traces.

_(pending)_
