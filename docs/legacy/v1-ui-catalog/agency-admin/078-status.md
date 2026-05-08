---
canonical_id: agency-admin/078-status
route: /quickbooks/status/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — JSON endpoint reporting QuickBooks connection state; the captured WebP is the browser's raw-JSON view (`{"connected": false}` for the catalog fixture without an active connection).

**Interaction notes:**
- Endpoint → `quickbooks_status` returns JSON with the `connected` boolean and, when active, the `company_name` and `connected_at` fields.
- Used by → admin pages to render the connection indicator on [agency-admin/068-invoices](068-invoices.md) (the "QuickBooks Not Connected" panel) and to gate per-row "Send to QuickBooks" CTAs.
- Polling → admin pages poll this endpoint after a successful OAuth flow at [agency-admin/076-callback](076-callback.md) to refresh the indicator without a full page reload.
- Inactive state → returns `{"connected": false}` (the captured response); active state returns `{"connected": true, "company_name": "...", "connected_at": "..."}`.
- Untrusted output → consumers must HTML-escape the company-name field before rendering it inside the indicator.
