---
canonical_id: family-member/002-client
route: /family/client/<int:client_id>/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — captured page is a Django `DEBUG=True` 404.

**Interaction notes:**
- GET `/family/client/<int:client_id>/` → 404. ⚠ inventory mismatch: real path is `/dashboard/family/client/<int:client_id>/` per `dashboard/urls.py:16`. View is `family_client_detail` (`dashboard/views.py:180`).
- GET the real URL → renders weekly/daily calendar, today's events, messages, billing summary, visit notes, care team, and family-visibility-approved chart comments. Hydration via `FamilyPortalService` + `CareRequestService`.
- ⚠ destructive: POST to the real URL → submits a care-request message; gated by `can_message_caregivers`, rate-limited 5/min. Skipped by crawler. Chart-comment family-views logged via `ChartCommentService.log_family_view`; route itself has no audit.
