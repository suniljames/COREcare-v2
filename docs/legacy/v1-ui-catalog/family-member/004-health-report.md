---
canonical_id: family-member/004-health-report
route: /family/client/<int:client_id>/health-report/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — captured page is a Django `DEBUG=True` 404.

**Interaction notes:**
- GET `/family/client/<int:client_id>/health-report/` → 404. ⚠ inventory mismatch: real path is `/dashboard/family/client/<int:client_id>/health-report/` per `dashboard/urls.py:26`. View is `family_health_report_download` (`dashboard/views.py:459`).
- GET the real URL → returns a family-variant health-report PDF (browser initiates download). Query params: `day_window` ∈ {7, 14, 30, 90} + a section subset. Rate-limited 10/h per user. HIPAA-access-logged in v1.
- IDOR boundary → `FamilyPortalService.verify_access`. Family-variant differs from staff-facing health report — sections filtered to family-appropriate content per the service's section-filter logic.
