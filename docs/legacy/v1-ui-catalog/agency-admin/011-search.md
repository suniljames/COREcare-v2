---
canonical_id: agency-admin/011-search
route: /admin/view-as/search/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — JSON endpoint backing the View As hub's live search; the captured WebP is the browser's raw-JSON view (`{"results": []}` with the "Pretty-print" toggle visible at the top).

**Interaction notes:**
- Endpoint → `view_as_search` returns JSON results (`{"results": [...]}`) for users matching a `?q=` query, scoped to the staff caller's permitted-target set.
- Used by → the live search input on [agency-admin/004-hub](004-hub.md) / [agency-admin/007-select](007-select.md); each keystroke fires a debounced fetch and the hub re-renders its target cards inline.
- Empty result → returned as `{"results": []}` (the captured response); the consumer renders an "No matches" empty state in the dropdown.
- Permission scope → mirrors the per-target rule used by the start endpoint at [agency-admin/006-view-as](006-view-as.md); a staff caller cannot search for users they cannot impersonate.
- Untrusted output → consumers must HTML-escape any rendered fields; the JSON includes `display_name`, `email`, and `user_id` for each hit.
