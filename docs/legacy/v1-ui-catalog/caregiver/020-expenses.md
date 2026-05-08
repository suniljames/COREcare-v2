---
canonical_id: caregiver/020-expenses
route: /caregiver/expenses/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "+ New", "All"/"Pending"/"Approved"/"Reimbursed" filter pills, "Submit your first expense" empty-state CTA, "Pay Period Budget" header, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `my_expenses` (`caregiver_dashboard/views.py:1244`) lists the caregiver's expense rows scoped to the current pay period; emits `Expense` rows excluding `DRAFT`.
- "Pay Period Budget" header ("$0.00 of $250.00 used") → reads from the active pay-period budget configuration; "$250.00 left" status copy reflects unused balance.
- Status filter pills → re-render with a `?status=` query (GET); populated render highlights the active pill.
- "+ New" header CTA / "Submit your first expense" empty-state CTA → [caregiver/019-submit](019-submit.md).
- Per-row card (populated render) → `/caregiver/expenses/<int:expense_id>/edit/` (out of catalog scope).
- "No expenses found." empty state → fixture caregivers without any submitted expenses.
