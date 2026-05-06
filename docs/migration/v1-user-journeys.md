# V1 User Journeys

> **Read [`README.md`](README.md) first.** It locks every convention used here.

This document narrates end-to-end user flows in v1, persona by persona. Each journey opens with a one-sentence "what / who / why," followed by a numbered route trace, qualitative side effects (DB writes, notifications, emails), and a one-line "failure-mode UX" call-out where v1 has notable behavior under failure (offline, server error, missing data).

Each journey **cites pages-inventory anchors** rather than redefining route facts. If a route mentioned here is not yet a row in [`v1-pages-inventory.md`](v1-pages-inventory.md), that's a coverage gap to fix.

**Status:** SCAFFOLDED. Persona sections and journey lists are in place; journey content is pending authoring against the [pinned v1 commit](README.md#v1-reference-commit).

---

## Conventions

- **Route trace:** numbered list of routes the user passes through, each linked to the corresponding pages-inventory row.
- **Side effects:** DB writes / notifications / emails / external-service calls described qualitatively (`creates a Visit record`, `fires a caregiver-assignment notification`), not at schema level.
- **Failure-mode UX:** one-line description of what the user sees when the path fails. Examples: `If clock-in fails offline, v1 queues locally and replays on reconnect.` `If credential expiry advances mid-page, v1 hides the page and routes to renewal.`
- **Tenant context:** included only where ambiguous (e.g., super-admin impersonating an agency admin).
- **Quoted v1 UI strings:** blockquoted with `v1 displays:` attribution.

---

## Super-Admin

_last reconciled: 2026-05-06 against v1 commit `9738412`_

### Agency management — _pending content authoring_
### View-As impersonation with audit trail — _pending content authoring_

---

## Agency Admin

_last reconciled: 2026-05-06 against v1 commit `9738412`_

### Client intake — _pending content authoring_
### Caregiver onboarding — _pending content authoring_
### Weekly timesheet review and approval — _pending content authoring_
### Invoice generation — _pending content authoring_
### Credential expiry handling — _pending content authoring_

---

## Care Manager

_last reconciled: 2026-05-06 against v1 commit `9738412`_

### Care plan authoring — _pending content authoring_
### Team oversight — _pending content authoring_

---

## Caregiver

_last reconciled: 2026-05-06 against v1 commit `9738412`_

### Clock in and out at a shift — _pending content authoring_
### Chart note submission — _pending content authoring_
### Expense submission — _pending content authoring_
### Schedule view — _pending content authoring_

---

## Client

_last reconciled: 2026-05-06 against v1 commit `9738412`_

### Care plan view — _pending content authoring_
### Upcoming shift view — _pending content authoring_

---

## Family Member

_last reconciled: 2026-05-06 against v1 commit `9738412`_

### Invite redemption — _pending content authoring_
### Recent visit notes view — _pending content authoring_
### Agency messaging — _pending content authoring_
