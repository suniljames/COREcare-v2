---
canonical_id: agency-admin/076-callback
route: /quickbooks/callback/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "stand-in" — the captured WebP shows the admin index with a red "Invalid OAuth state. Please try connecting again." banner (see Interaction notes for context).

**Interaction notes:**
- Endpoint → `quickbooks_callback` handles the OAuth callback from Intuit; exchanges the auth code for tokens and saves the active `QuickBooksConnection` row.
- Successful callback → ⚠ destructive: writes the connection row + OAuth tokens, deactivates any prior connection, and redirects to the admin index with a success flash that shows the connected QuickBooks company name. Skipped by crawler in the captured run because no valid OAuth state was present.
- State validation → checks the session-bound OAuth state against the `state` query parameter; mismatch produces the captured "Invalid OAuth state" banner without writing tokens.
- Token storage → tokens are stored encrypted at rest; the connection row records `connected_at` for the status surface.
- Sibling routes → connect at [agency-admin/075-connect](075-connect.md), disconnect at [agency-admin/077-disconnect](077-disconnect.md), status at [agency-admin/078-status](078-status.md).
