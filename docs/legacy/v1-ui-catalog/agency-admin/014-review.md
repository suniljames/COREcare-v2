---
canonical_id: agency-admin/014-review
route: /admin/expenses/review/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "PENDING" / "APPROVED" stat cards, "By Employee" / "By Offer" tab toggle, "Filter" search input, "No expenses found for this filter." empty state, "View all" link, "Home"/"Schedule"/"Earnings"/"Profile" bottom-nav, "Logout" header link.

**Interaction notes:**
- Page load → `admin_expense_review` (`dashboard/admin_expense_review.html`) lists pending caregiver expense submissions awaiting Agency Admin approval, with submitter, amount, category, and attached receipts surfaced per row in the populated render.
- "PENDING" / "APPROVED" stat cards → counters across the active filter window.
- "By Employee" / "By Offer" tab toggle → switches between caregiver-grouped and offer-grouped renderings.
- "Filter" → narrows the visible list by free-text match (server-side filter on submit).
- "View all" link → drops filters and shows the full review queue.
- Per-row approve / reject actions → drill to single-expense routes (out of catalog scope: `/admin/expenses/review/<int:expense_id>/approve/` and the matching reject endpoint), each ⚠ destructive POST that mutates the `Expense.status` and routes the row to reimbursement when approved.
