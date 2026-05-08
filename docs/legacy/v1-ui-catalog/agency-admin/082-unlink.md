---
canonical_id: agency-admin/082-unlink
route: /quickbooks/clients/<int:client_id>/unlink/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint that returns JSON; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing.

**Interaction notes:**
- Endpoint → `quickbooks_client_unlink` removes the QuickBooks customer link from a COREcare client; clears all link metadata fields.
- ⚠ destructive: POST → zeros `qb_customer_id` and the display-name snapshot on the `Client` row; audit-logs the actor + before-state. Skipped by crawler.
- Not-linked guard → returns a JSON `not-linked` error when the client has no active QuickBooks binding.
- History preservation → historical invoice logs (written by [agency-admin/079-send-invoice](079-send-invoice.md)) keep their pinned QB customer reference; the unlink only affects future sends.
- Re-link → after an unlink, the admin can pick a new QB customer via [agency-admin/080-search](080-search.md) and [agency-admin/081-link](081-link.md).
- Permissions → guarded by the agency-admin billing-management capability; non-admin callers receive a permission error without mutating state.
