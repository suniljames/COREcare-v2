---
canonical_id: agency-admin/075-connect
route: /quickbooks/connect/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "stand-in" — the captured WebP shows the admin index with a red "QuickBooks is not configured. Set QUICKBOOKS_CLIENT_ID + QUICKBOOKS_CLIENT_SECRET + QUICKBOOKS_REDIRECT..." banner (see Interaction notes for context).

**Interaction notes:**
- Endpoint → `quickbooks_connect` initiates the QuickBooks Online OAuth flow; redirects an Agency Admin to Intuit's consent screen when env credentials are set.
- ⚠ destructive: GET → on success, generates an OAuth state token, persists it to the session, and redirects to Intuit. Skipped by crawler in the captured run because env credentials were unset and the view aborted with the configuration banner.
- Configuration prerequisites → `QUICKBOOKS_CLIENT_ID`, `QUICKBOOKS_CLIENT_SECRET`, `QUICKBOOKS_REDIRECT_URI` must all be set; the absence of any one renders the captured stand-in.
- OAuth callback → handled by [agency-admin/076-callback](076-callback.md), which exchanges the auth code for tokens and saves the active `QuickBooksConnection` row.
- Status check → exposed via [agency-admin/078-status](078-status.md) (JSON connected boolean + connected company name).
