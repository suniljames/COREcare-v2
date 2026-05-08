---
canonical_id: agency-admin/018-role-permissions
route: /admin/role-permissions/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Role Permissions" header, "Control what each role can do — changes take effect immediately." subtitle, "CLINICAL" / "FINANCIAL" / "ISSUE" category sections, per-row capability label with role-column toggles ("ADMIN", "CARE MANAGER", "CAREGIVER", "FAMILY"), per-row tooltip "?" hint, "Logout" header link.

**Interaction notes:**
- Page load → `role_permissions` (`admin/role_permissions.html`) renders the role × capability matrix; toggle states reflect the active grant per role (green = granted, off = denied).
- Per-row toggle → ⚠ destructive: fires a POST to [agency-admin/019-toggle](019-toggle.md) flipping the single capability bit for the targeted role. Audit-logged. Skipped by crawler.
- Subtitle promise → "changes take effect immediately" is enforced by the toggle endpoint (no confirm dialog); revoking a capability invalidates dependent server-side checks on the next request.
- Category groupings ("CLINICAL", "FINANCIAL", "ISSUE", etc.) → drive the v2 capability schema split between PHI-bearing and operational controls.
- "?" tooltip per row → surfaces the capability description and the matching server-side check call site for v1 reviewers.
