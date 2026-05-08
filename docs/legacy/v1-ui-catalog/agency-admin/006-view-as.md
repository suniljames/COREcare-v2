---
canonical_id: agency-admin/006-view-as
route: /admin/view-as/<int:user_id>/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "stand-in" — the captured WebP shows the admin index with a "You are not authorized to view as this user" red banner; the actual route renders the step-up confirmation form when the staff caller is permitted to impersonate the target. See [agency-admin/008-caregiver](008-caregiver.md) for the equivalent caregiver-target step-up form (real UI capture).

**Interaction notes:**
- Endpoint → `view_as_start` redirects unpermitted staff callers back to the admin index with the "You are not authorized to view as this user" flash visible in this capture; permitted callers see the step-up confirmation form (target identity, "Read-Only Mode" warning, "Confirm your password", "Reason Category" select, "Reason Details" textarea).
- ⚠ destructive: the step-up POST → starts a `ViewAsSession` row, audit-logs the initiator + target + reason, and rotates the session into impersonation mode for the configured duration. Skipped by crawler.
- Permissions → guarded by `is_staff` + per-target permission policy; the fixture's `is_superuser` test user can impersonate the family-member target shown in [agency-admin/005-select](005-select.md) but not arbitrary user ids, which is why the captured response is the deny-stand-in.
- Session end → [agency-admin/009-end](009-end.md). All sessions are HIPAA-audit-logged at [agency-admin/013-audit-log](013-audit-log.md).
