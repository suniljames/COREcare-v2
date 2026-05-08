---
canonical_id: agency-admin/039-review-queue
route: /charting/comments/review-queue/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Comment Review Queue" header, "0 comments pending review" subtitle, "No comments awaiting approval." empty state, "Logout" header link.

**Interaction notes:**
- Page load → `chart_comment_review_queue` (`charting/comment_review_queue.html`) lists chart comments awaiting family-visibility approval, filterable by client.
- Per-row approve / reject (populated render) → ⚠ destructive POSTs that mutate the comment's `family_visibility` flag; audit-logged with reviewer + decision + timestamp. Skipped by crawler.
- Per-row drill-in → opens the matching `DailyChart` so the reviewer can see context before deciding.
- Empty state → fixture has no comments awaiting approval; populated render shows pending comments with chart context, submitter, content, and the family-visibility flag plus a free-text annotation field.
- Audit usage → reviewer decisions are surfaced in the family-visibility log (`ChartCommentService.log_family_view`) when a family member later opens the chart.
