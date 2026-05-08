---
canonical_id: care-manager/005-edit
route: /care-manager/expenses/<int:expense_id>/edit/
persona: Care Manager
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Type" select, "Out of Pocket" toggle, "Company Card" toggle, "Choose File", "Resubmit", "Back to My Expenses".

**Interaction notes:**
- Page load → renders the `cm_edit_expense` view (`care_manager/views.py:630`). The page title reads "Resubmit Expense" when the expense status is `REJECTED`; the rejection-reason banner at the top displays `Expense.rejection_reason` verbatim. The form mirrors the submit page (`Type`, `Amount ($)`, `Date`, `Description`, `Client (optional)`, `Payment Method`, `Receipt`, `Notes`) with values pre-filled from the existing expense; the Client field is locked to the originally-linked client.
- "Receipt" section → reads "Current receipt attached. Upload a new one to replace it." when `Expense.receipts` is non-empty. The "Choose File" picker is optional on edit; submitting without a file preserves the existing receipt. Submitting with a file deletes the previous receipt rows (`expense.receipts.all().delete()`) and inserts a fresh `ExpenseReceipt` per `cm_edit_expense` lines 674–679.
- ⚠ destructive: "Resubmit" button → POSTs to `/care-manager/expenses/<id>/edit/`. For `REJECTED` status the handler calls `ExpenseService.resubmit_expense`; otherwise it calls `ExpenseService.edit_expense`. Both audit-log via the workflow-event service. Skipped by crawler.
- "Back to My Expenses" link → navigates to [care-manager/003-expenses](003-expenses.md).

Submitter-only ownership is enforced at the queryset level (`get_object_or_404(Expense, pk=expense_id, submitter=request.user)`) — non-submitter access raises `Http404`. Edit eligibility is gated by `expense.can_edit` (raises `PermissionDenied` if the status disallows edit).
