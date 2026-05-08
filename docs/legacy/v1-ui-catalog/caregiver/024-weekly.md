---
canonical_id: caregiver/024-weekly
route: /caregiver/weekly/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Back to Schedule", "Previous", "Week (Mon-Sun)" header with date range, "No visits recorded" empty-state copy, header "Logout".

**Interaction notes:**
- Page load → `weekly_summary` (`caregiver_dashboard/views.py:1475`) renders the printable weekly payroll summary for the selected Mon–Sun window: per-visit hours + reimbursements rolled up to weekly totals.
- "Previous" → re-renders the prior week (GET).
- "No visits recorded" empty state → fixture caregivers without `Visit` rows in the active week. Populated render shows a per-visit table with date, client, scheduled vs. clock-in/out, hours, and reimbursements.
- "Back to Schedule" → [caregiver/004-schedule](004-schedule.md).
- Adjacent download routes → [caregiver/025-csv](025-csv.md) and [caregiver/026-pdf](026-pdf.md); both export the same week range as binary attachments rather than HTML.
