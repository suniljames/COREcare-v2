---
canonical_id: caregiver/023-earnings
route: /caregiver/earnings/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "This Week"/"Last Week"/"Month" tab toggle, "Previous"/"Next" week paginator, per-day rows ("No shifts" empty state), "Download CSV", "Download PDF", "My Expenses" cell with chevron, "Final amounts may differ after payroll review." disclaimer, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `earnings_dashboard` (`caregiver_dashboard/views.py:1429`) renders week-level earnings with per-day shift summaries.
- "This Week" / "Last Week" / "Month" → re-render with a `?range=` query (GET).
- "Previous" / "Next" → step the visible week range (GET).
- "Download CSV" → [caregiver/025-csv](025-csv.md). "Download PDF" → [caregiver/026-pdf](026-pdf.md).
- "My Expenses" cell → [caregiver/020-expenses](020-expenses.md).
- "Final amounts may differ after payroll review." disclaimer → dashboard reflects worked hours only; differential, reimbursement, and PTO adjustments land at payroll close.
