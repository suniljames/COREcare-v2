---
canonical_id: super-admin/001-kill-all
route: /admin/view-as/kill-all/
persona: Super-Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint with no GET handler; the captured screenshot is the empty 405 response.

**Interaction notes:**
- ⚠ destructive: POST to this URL → expires every active `ViewAsSession` row, audit-logs a warning (`View As emergency kill switch activated`), and redirects to the Django admin index. The trigger lives on [agency-admin/013-audit-log](../agency-admin/013-audit-log.md) as a red `Kill All Active Sessions` button gated by `is_superuser`; the button form uses a JavaScript `confirm()` dialog before submitting. Skipped by crawler — the route is GET-405.
