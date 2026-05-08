---
canonical_id: family-member/004-health-report
route: /dashboard/family/client/<int:client_id>/health-report/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — PDF download endpoint with no rendered UI.

**Interaction notes:**
- GET this URL → with sufficient recent health data, response is a family-variant health-report PDF (browser download). Without enough data, response body is plain text `There isn't enough recent health data to generate a report right now. Data will be available after the next visit.` (the captured state). View is `family_health_report_download` (`dashboard/views.py:459`).
- Query params → `day_window` ∈ {7, 14, 30, 90} sets the lookback; a section subset filters output. Family-variant filters sections to family-appropriate content.
- IDOR boundary → `FamilyPortalService.verify_access`. Rate-limited 10/h per user; HIPAA-access-logged in v1.
