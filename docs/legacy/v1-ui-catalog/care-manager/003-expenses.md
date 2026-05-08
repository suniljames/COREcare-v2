---
canonical_id: care-manager/003-expenses
route: /care-manager/expenses/
persona: Care Manager
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Logout", "+ New", "Submit your first expense".

**Interaction notes:**
- "+ New" → navigates to [care-manager/004-submit](004-submit.md).
- "Submit your first expense" → navigates to [care-manager/004-submit](004-submit.md). Empty-state link; only renders when the user has zero expenses.
- "Logout" → ends the session and redirects to login.
- Page load → `cm_expenses` view (`care_manager/views.py:546`) hydrates `ExpenseService.get_budget_status` and `ExpenseService.get_expenses_by_client`. Captured fixture has no expenses, so the body shows the budget card (`$0.00 of $250.00`), a status legend (Pending/Approved/Reimbursed/Rejected), and a `No expenses yet.` empty card. Otherwise renders per-client groups with status badges, amounts, dates, and receipt thumbnails.
