---
canonical_id: agency-admin/010-status
route: /admin/view-as/status/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — JSON endpoint that returns active View As session state; the captured WebP is the browser's raw-JSON view (`{"is_view_as": false}` with the "Pretty-print" toggle visible at the top).

**Interaction notes:**
- Endpoint → `view_as_status` returns JSON with the impersonation flag (`is_view_as`) and, when active, the target identity + elapsed time. The captured response is the inactive state (`false`) because the staff user had no active session at crawl time.
- Used by → the impersonation banner JS and middleware to render the warning bar across staff pages while a session is active.
- Polling → admin pages poll this endpoint to surface a session-expired toast when the configured duration elapses; rate-limit detail surfaces in [agency-admin/012-stats](012-stats.md).
- Active state → returns the target user id + display identity so the banner can render a "Viewing as ..." prefix; consumers should treat the JSON as untrusted and HTML-escape any rendered fields.
- Session start → lives at [agency-admin/006-view-as](006-view-as.md) / [agency-admin/008-caregiver](008-caregiver.md); end at [agency-admin/009-end](009-end.md).
