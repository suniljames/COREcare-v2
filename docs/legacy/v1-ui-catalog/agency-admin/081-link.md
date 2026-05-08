---
canonical_id: agency-admin/081-link
route: /quickbooks/clients/<int:client_id>/link/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint that returns JSON; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing.

**Interaction notes:**
- Endpoint → `quickbooks_client_link` links a COREcare client to a QuickBooks customer ID for reliable invoice creation (Issue #329 lineage).
- ⚠ destructive: POST → writes the `qb_customer_id` + display-name snapshot onto the `Client` row; audit-logs the actor + before-state (none or prior link) + after-state. Skipped by crawler.
- Duplicate-link guard → returns a JSON error naming the conflicting COREcare client when the same QB customer is already linked elsewhere (one-to-one binding).
- Pre-link search → the QB-customer ID is typically picked from [agency-admin/080-search](080-search.md), but an admin can also enter the ID directly when copying it from QuickBooks.
- Effect on send-invoice → with a link in place, [agency-admin/079-send-invoice](079-send-invoice.md) skips the customer-search step and posts the invoice straight to the bound customer.
- Unlink → [agency-admin/082-unlink](082-unlink.md) clears the binding without affecting historical invoice logs.
