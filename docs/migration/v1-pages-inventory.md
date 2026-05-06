# V1 Pages Inventory

> **Read [`README.md`](README.md) first.** It locks every convention used here: persona vocabulary, v2-status enum, severity rubric, visual markers, PHI placeholder set, voice, anchor stability, v1 commit pin.

This document is the **authoritative route catalogue** for v1's customer-facing surface. Every other doc in this set cites into it; do not redefine routes elsewhere. One row per (route, persona) tuple — a route accessible to multiple personas appears in multiple rows.

**Status:** SCAFFOLDED. Persona sections are in place; rows are pending content authoring against `suniljames/COREcare-access` at the [pinned commit](README.md#v1-reference-commit). Until rows are filled, the [`v1-functionality-delta.md`](v1-functionality-delta.md) is the most complete view of v1's feature surface.

---

## Coverage

- **Denominator** (distinct v1 URL patterns rendering HTML, per the rules in [README §Coverage target](README.md#coverage-target)): _to be measured against the pinned commit_.
- **Numerator** (rows present below): 0.
- **Coverage:** 0% (target ≥95%).

---

## Schema

Each persona section below uses this row schema. Authors: do not add or remove columns without updating [README §Locked conventions](README.md#locked-conventions) and the structure check.

| Field | Description |
|-------|-------------|
| `route` | URL pattern (kebab-case where v1 used it; otherwise the literal Django path) |
| `purpose` | What the page is for, ≤80 chars |
| `what_user_sees_can_do` | Key data + primary actions, ≤2 lines |
| `v2_status` | `implemented` / `scaffolded` / `missing` |
| `severity` | `H` / `M` / `L` / `D` (only when `v2_status=missing`) |
| `multi_tenant_refactor` | `true` if v1 single-tenant assumption requires v2 rework |
| `rls_bypass_by_design` | `true` for Super-Admin / View-As impersonation surfaces |
| `phi_displayed` | `true` if route renders any PHI in v1 |
| `screenshot_ref` | filename in `docs/legacy/v1-ui-catalog/<persona>/` once #79 lands; otherwise `not_screenshotted: <reason>` |
| `v2_link` | Single canonical repo-relative path when `v2_status` ≠ `missing` |

---

## Super-Admin

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Super-Admin pages are platform-operator surfaces that bypass tenant isolation by design. v1 was single-tenant per install, so v1's "super-admin" features sit at the elitecare project level (cross-agency Django admin views, support tooling, View-As impersonation). v2 must preserve every audit-log behavior on these routes — RLS bypass is a load-bearing control, not a convenience.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Agency Admin

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Agency Admin pages cover scheduling, billing, payroll, credentialing, compliance, and team oversight. This is v1's largest surface and v2's highest-volume rebuild target.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Care Manager

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Care Manager pages cover care plan authoring, supervisory review, and team-level oversight of caregivers. Distinct from Agency Admin in clinical scope; distinct from Caregiver in supervisory authority.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Caregiver

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Caregiver pages are field-facing: clock-in/out, schedule view, chart-note submission, expense submission, profile and credentials. Highest-volume, lowest-patience persona. Mobile-first ergonomics matter most here.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Client

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Client pages cover the care recipient's view of their care plan, upcoming shifts, and assigned caregivers. Lower frequency than Caregiver; PHI handling is paramount because the client is the subject.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Family Member

_last reconciled: 2026-05-06 against v1 commit `9738412`_

Family Member pages cover the limited-visibility view granted to a client's authorized representative. Invite redemption, recent visit notes, agency messaging. Lowest frequency; gaps here are the hardest to detect and easiest to silently drop.

| route | purpose | what_user_sees_can_do | v2_status | severity | multi_tenant_refactor | rls_bypass_by_design | phi_displayed | screenshot_ref | v2_link |
|-------|---------|-----------------------|-----------|----------|-----------------------|----------------------|---------------|----------------|---------|
| _(rows pending content authoring)_ | | | | | | | | | |

---

## Shared routes

Routes accessible by more than one persona appear once per persona above with a cross-reference note. This section will list them once row authoring is complete.

_(pending content authoring)_
