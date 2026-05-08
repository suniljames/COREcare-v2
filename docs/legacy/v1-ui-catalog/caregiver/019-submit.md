---
canonical_id: caregiver/019-submit
route: /caregiver/expenses/submit/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "My Expenses" back-link, "Expense Type" select, "Amount ($)", "Date of Expense", "Description", "Client (optional)" select, "Choose File" (receipt), "Additional Notes", "Submit Expense" orange button, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `submit_expense` (`caregiver_dashboard/views.py:1167`) renders the standalone reimbursement form (Issue #602); displays remaining pay-period budget at the top.
- "Submit Expense" → ⚠ destructive: POSTs multipart form to create an `Expense` row in `SUBMITTED` state with the receipt file attached. Skipped by crawler.
- Receipt rules → photo or PDF, 5 MB max; `"Do not include client health information (PHI) in receipts."` copy is rendered next to the file input as a hard rule.
- "Client (optional)" select → populated from the caregiver's assigned clients; submitting without a selection leaves the expense unattributed.
- "Recent Expenses" footer block → lists submitted expenses (empty state shown for fixture state); populated render shows a per-row status pill.
- "My Expenses" back-link → [caregiver/020-expenses](020-expenses.md).
