---
canonical_id: agency-admin/062-timecards
route: /dashboard/admin/timecards/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Back to Admin" link, "Staff Timecards" header, "View" select (default "Weekly"), week paginator ("<" / "May 04 - May 10, 2026" / ">"), "PDF" / "CSV" export buttons, "STAFF ACTIVE" / "ACTUAL HOURS" / "TOTAL PAYROLL" stat cards, "Caregivers" header strip, "Logout" header link.

**Interaction notes:**
- Page load → `admin_timecard_summary` (`dashboard/admin_timecard_summary.html`) lists payroll-period timecard summary across all caregivers.
- "View" select → switches the period (Weekly / Monthly / Yearly); each option re-renders with adjusted aggregation.
- Week paginator → steps the visible window (GET).
- "PDF" → renders a printable summary; "CSV" exports the raw rows for the active period; both bypass the per-caregiver detail.
- Per-caregiver row drill-in → [agency-admin/063-timecards](063-timecards.md), the individual caregiver's timecard detail.
- Stat cards → roll-ups across the active period: STAFF ACTIVE counts caregivers with at least one visit, ACTUAL HOURS sums clocked time, TOTAL PAYROLL sums shift earnings + reimbursements.
