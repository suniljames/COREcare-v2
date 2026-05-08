---
canonical_id: agency-admin/080-search
route: /quickbooks/customers/search/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — JSON endpoint backing the link-customer modal; the captured WebP is the browser's raw-JSON view (`{"success": false, "error": "Search query must be at least 2 characters"}` for the bare-GET probe).

**Interaction notes:**
- Endpoint → `quickbooks_customers_search` returns a JSON list of QB customers matching a `?q=` query, with display name, email, phone, and balance per hit.
- Used by → the link-customer modal in the per-client admin view; each keystroke fires a debounced fetch and the modal re-renders the candidate list.
- Min query length → 2 characters; shorter queries return the captured `{"success": false, "error": "Search query must be at least 2 characters"}` response without hitting the QB API.
- API quota → results are pulled live from QuickBooks per call; consider caching at the consumer when the modal stays open.
- Pick → selecting a result drives [agency-admin/081-link](081-link.md), which writes the COREcare-client → QB-customer binding.
- Untrusted output → consumers must HTML-escape every result field before rendering inside the modal.
