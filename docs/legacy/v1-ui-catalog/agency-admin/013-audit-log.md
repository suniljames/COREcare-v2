---
canonical_id: agency-admin/013-audit-log
route: /admin/view-as/audit-log/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "View As Audit Log" header, "HIPAA-compliant audit trail" subtitle, "Total Sessions (Last 100)" stat card, "Active Sessions" panel, audit table header ("STARTED" / "INITIATED BY" / "VIEWING AS" / "STATUS"), "No View As session(s)" empty-state copy, "HIPAA Compliance Note" disclosure block, "Logout" header link.

**Interaction notes:**
- Page load → `view_as_audit_log` (`core/view_as_audit_log.html`) renders the chronological audit trail of every View As session (start, end, forbidden-action attempt) with filters for initiator, target, and date.
- Per-row drill-in → opens the matching session's full action trail (page views, including IP and user-agent), retained for 6 years per HIPAA per the disclosure block.
- "HIPAA Compliance Note" → reminds the auditor that all session activity is logged and that detailed page-view logs are accessible via the per-session drill.
- Empty state → "No View As session(s)" because the fixture's `is_superuser` test user has not started any sessions; populated rendering shows one row per session with status pill + per-row drill-in link.
- "Kill All Active Sessions" → red button gated by `is_superuser` is rendered on this page; it triggers [agency-admin/100-kill-all](100-kill-all.md) (POST-only emergency kill switch).
