---
canonical_id: agency-admin/047-approval-queue
route: /charting/reports/approval-queue/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Report Approval Queue" header, "No pending report requests." empty state, "Logout" header link.

**Interaction notes:**
- Page load → `admin_report_approval_queue` (`charting/admin_report_approval_queue.html`) lists caregiver-initiated health-report requests awaiting approval before family delivery.
- Per-row drill-in (populated render) → opens the approve / reject endpoint at `/charting/reports/approval/<int:request_id>/` (POST-only, out of catalog scope); the approval action redirects back to this queue with a success or error flash.
- ⚠ destructive: per-row approve / reject → mutates the `ReportRequest.status`, audit-logs the reviewer + decision + optional annotation, and on approve fires the family-facing email or download flow.
- Empty state → fixture has no pending caregiver-initiated requests; populated render shows submitter, client, and the section list each request asked for.
- Origin → caregivers create the requests via [caregiver/028-new](../caregiver/028-new.md); the queue is the operator gate before family delivery.
