# V1 Integrations and Exports

> **Read [`README.md`](README.md) first.** It locks every convention used here.

This document inventories everything v1 talks to outside its own database: external integrations (third-party SaaS), the internal notification and email backend (because it's a customer-visible side channel that can silently break on rebuild), and customer-facing exports (CSV, PDF, accounting hand-offs). Anything that fires when an end-user takes an action in v1 is in scope.

**Status:** SCAFFOLDED. Sub-section structure is in place; entries are pending authoring against the [pinned v1 commit](README.md#v1-reference-commit).

---

## Schema

| Field | Description |
|-------|-------------|
| `name` | Integration or export name |
| `vendor_or_internal` | Stripe, Twilio, SendGrid, QuickBooks, internal, etc. |
| `trigger` | What action or schedule fires it (user click, cron job, webhook, etc.) |
| `direction_and_sync` | `inbound` / `outbound`; `sync` / `async` |
| `surfaces_at_routes` | Anchor links into pages-inventory rows where users encounter the integration in the UI |
| `customer_visibility` | What end-users see (a banner, an email, a downloaded file, nothing) |
| `v2_status` | `implemented` / `scaffolded` / `missing` |
| `severity` | `H` / `M` / `L` / `D` (only when `v2_status=missing`) |

---

## External integrations

Third-party SaaS v1 integrates with. Sub-grouped by vendor.

### Billing and payments

_(entries pending content authoring)_

### Payroll

_(entries pending content authoring)_

### Accounting

_(entries pending content authoring)_

### Messaging and notifications (third-party)

_(entries pending content authoring)_

### Identity, auth, and SSO (third-party)

_(entries pending content authoring)_

### Other

_(entries pending content authoring)_

---

## Internal notification and email backend

v1's own notification system and email-sending pipeline. Customer-visible side channels that aren't third-party but can silently break on rebuild if undocumented.

### Email pipeline

_(entries pending content authoring — covers SMTP/transactional templates v1 ships, send-on-failure retry behavior, and any email-reliability tracking documented as a gap in `v1-functionality-delta.md`)_

### In-app notifications

_(entries pending content authoring — covers v1's notification inbox, push subscriptions if any, and unread-count semantics)_

---

## Customer-facing exports

User-triggered or scheduled exports that produce a file or feed visible to a customer.

### CSV exports

_(entries pending content authoring)_

### PDF exports

_(entries pending content authoring)_

### Other formats

_(entries pending content authoring)_

---

## Cross-references

Every entry above that surfaces in the UI must link to its pages-inventory rows in `surfaces_at_routes`. Once authoring completes, this section will list any orphan integrations (no UI surface) explicitly.

_(pending)_
