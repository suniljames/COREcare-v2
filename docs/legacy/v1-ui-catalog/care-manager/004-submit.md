---
canonical_id: care-manager/004-submit
route: /care-manager/expenses/submit/
persona: Care Manager
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Logout", "Out of Pocket", "Company Card", "Choose File", "Submit Expense", "Back to My Expenses".

**Interaction notes:**
- "Submit Expense" → POSTs here. `cm_submit_expense` (`care_manager/views.py:567`) calls `ExpenseService.create_expense`, attaches an `ExpenseReceipt`, flashes success, redirects to [care-manager/003-expenses](003-expenses.md). Audit-logged.
- "Out of Pocket" / "Company Card" → toggle `payment_method`; `Out of Pocket` selected here.
- "Choose File" → file picker (photo or PDF, max 5MB).
- "Back to My Expenses" → [care-manager/003-expenses](003-expenses.md).
- Page load → `cm_submit_expense.html` with budget banner + `ExpenseSubmitForm`. "Client (optional)" select is empty — the fixture's CM has no assigned clients.
