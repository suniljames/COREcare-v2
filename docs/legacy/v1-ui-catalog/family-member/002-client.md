---
canonical_id: family-member/002-client
route: /dashboard/family/client/<int:client_id>/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Back to List", "Schedule"/"Daily Charts"/"Receipts" tabs, "Request Care", "Consult Concierge", "Send Message", "Download PDF", "Download Report", "Log out".

**Interaction notes:**
- Tabs → switch section; hydrated via `FamilyPortalService`.
- "Send Message" → ⚠ destructive: POSTs a care-request; `can_message_caregivers`-gated, 5/min rate-limited. Skipped by crawler.
- "Download PDF" / "Download Report" → work-hours PDF + [family-member/004-health-report](004-health-report.md).
- "Back to List" → [family-member/001-dashboard](001-dashboard.md).
- Page load → `family_client_detail` (`dashboard/views.py:180`) renders calendar, events, messages, billing, visit notes, care team, family-visibility chart comments (logged via `ChartCommentService.log_family_view`).
