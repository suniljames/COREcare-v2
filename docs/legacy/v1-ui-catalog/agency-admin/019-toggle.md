---
canonical_id: agency-admin/019-toggle
route: /admin/role-permissions/toggle/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — POST-only endpoint that returns a redirect; the captured WebP is the post-redirect blank state because the crawler's `intercept-non-GET` discipline prevents the POST from firing. The CTA that triggers this endpoint lives on [agency-admin/018-role-permissions](018-role-permissions.md) (per-row role-toggle switch).

**Interaction notes:**
- Endpoint → `role_permissions_toggle` (`admin/`) flips a single capability grant for a target role.
- ⚠ destructive: POST → mutates the role's capability set, audit-logs the actor + role + capability + new state, and redirects to [agency-admin/018-role-permissions](018-role-permissions.md). Skipped by crawler.
- Atomicity → each toggle is a single DB write per capability bit; no batch mode, so multiple toggles fire as separate requests.
- Permissions → guarded by the `manage_role_permissions` capability; non-admin callers receive 403 without mutating state.
- Idempotence → re-submitting the same toggle is a no-op against the current state (server reads current value, applies the requested target, audit-logs the diff).
