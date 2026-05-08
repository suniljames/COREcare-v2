---
canonical_id: agency-admin/008-caregiver
route: /admin/view-as/caregiver/<int:user_id>/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "View As" header, "YOU WILL BE VIEWING:" target identity card (caregiver name + email), "Read-Only Mode" warning panel, "Confirm your password" input, "Step-up authentication required" hint, "Reason Category" select (e.g., "Troubleshooting"), "Reason Details (optional)" textarea, "Start Session" submit button, "Logout" header link.

**Interaction notes:**
- Page load → `view_as_start_caregiver` (`core/view_as_start.html`) renders the step-up confirmation form for the caregiver target; the same template serves family-member step-up at [agency-admin/006-view-as](006-view-as.md).
- ⚠ destructive: form submit → starts a `ViewAsSession` row scoped to the target caregiver, audit-logs initiator + target + reason category + reason details, and rotates the session into impersonation mode. The "Read-Only Mode" warning makes clear that mutating actions are disabled while the session is active. Skipped by crawler.
- "Confirm your password" → re-authenticates the staff caller before the session opens (step-up auth, defense in depth against compromised cookies).
- "Reason Category" → constrained list (e.g., "Troubleshooting", "Audit", "Family Request") that the audit log indexes for HIPAA reporting.
- Session end → [agency-admin/009-end](009-end.md). Audit trail surfaces at [agency-admin/013-audit-log](013-audit-log.md).
