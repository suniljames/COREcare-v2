---
canonical_id: agency-admin/077-disconnect
route: /quickbooks/disconnect/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "stand-in" — the captured WebP shows the admin index because the disconnect endpoint is POST-only and the crawler's `intercept-non-GET` discipline prevents the POST from firing; a GET redirect lands on the admin home.

**Interaction notes:**
- Endpoint → `quickbooks_disconnect` deactivates every active `QuickBooksConnection` row for the agency.
- ⚠ destructive: POST → marks all active connection rows inactive, clears tokens (or zeroes them, retaining audit history), and redirects to the admin index with a "QuickBooks disconnected" success flash. Skipped by crawler.
- Idempotence → re-submitting against an already-disconnected agency is a no-op against state; still emits an audit-log row to capture the actor + timestamp.
- Reconnect → the admin must restart the OAuth flow at [agency-admin/075-connect](075-connect.md) to attach a new connection.
- Status check → [agency-admin/078-status](078-status.md) returns `{"connected": false}` after a successful disconnect.
