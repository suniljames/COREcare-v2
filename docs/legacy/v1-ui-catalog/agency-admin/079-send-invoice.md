---
canonical_id: agency-admin/079-send-invoice
route: /quickbooks/send-invoice/<int:client_id>/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint that returns JSON; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing.

**Interaction notes:**
- Endpoint → `quickbooks_send_invoice` sends a client's weekly invoice to QuickBooks; logs the send with a billing snapshot for audit (Issue #329 lineage).
- ⚠ destructive: POST → reads the active `QuickBooksConnection`, builds the invoice payload, calls Intuit's API, writes a `QuickBooksInvoiceLog` row with the billing snapshot, and returns JSON success or a detailed error referencing the client. Skipped by crawler.
- Required state → an active QuickBooks connection ([agency-admin/078-status](078-status.md) returns `connected: true`) AND a client-to-QB-customer link ([agency-admin/081-link](081-link.md)).
- Error responses → include hints to relink (when the QB customer reference is stale) or to create a customer in QuickBooks (when no candidate matches a search via [agency-admin/080-search](080-search.md)).
- Optional override → POST body accepts a `qb_customer_id` to override the linked customer for ad-hoc routing without creating a permanent link.
- Audit trail → the billing snapshot pinned at send time guarantees that subsequent invoice changes don't retro-mutate the sent record.
