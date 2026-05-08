---
canonical_id: caregiver/027-reports
route: /caregiver/reports/
persona: Caregiver
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "+ New Report" header CTA, "No reports yet" empty-state copy, "Generate your first report" inline link, bottom-nav "Home"/"Schedule"/"Earnings"/"Profile", header "Logout".

**Interaction notes:**
- Page load → `caregiver_reports_list` (`caregiver_dashboard/views.py:2947`) lists the caregiver's self-service reports (Issue #1046 Phase 2); rows surface report type, generated date, and per-row preview/download actions in the populated render.
- "+ New Report" / "Generate your first report" → [caregiver/028-new](028-new.md).
- Empty state copy → fixture has no generated reports for this caregiver. Populated render links each row to `/caregiver/reports/<int:request_id>/preview/` and `/caregiver/reports/<int:request_id>/download/` (both out of catalog scope).
- "Logout" → POST sign-out (skipped by crawler).
