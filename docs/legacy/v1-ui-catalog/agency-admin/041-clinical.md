---
canonical_id: agency-admin/041-clinical
route: /charting/reports/<int:client_id>/clinical/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — direct PDF download endpoint that returns `application/pdf` with `Content-Disposition: attachment` for normal data ranges. The captured WebP is the plain-text fallback "No health data found for the selected date range." rendered by the view when the client has no chart entries within the requested window.

**Interaction notes:**
- Endpoint → `clinical_health_report` returns the PDF directly (no preview), keyed on the client id and an optional `?days=` query (supported windows: 7, 14, 30, 90).
- Plain-text fallback → returned when `DailyChart` rows for the client + window are empty; the response body is the literal "No health data found for the selected date range." string captured in the WebP.
- ⚠ Crawler note → Playwright treats normal-data responses as downloads (`Content-Disposition: attachment`) and intercepts them without paint; the captured WebP only renders when the fallback fires.
- Reached from → [agency-admin/040-generate](040-generate.md) when the Clinical report-type radio is selected and the form posts directly to this URL with the `?days=` query.
- Permissions → guarded by Django's `@staff_member_required` decorator (the v1 view applies no finer-grained capability check); auditing fires for both successful PDF and fallback responses.
