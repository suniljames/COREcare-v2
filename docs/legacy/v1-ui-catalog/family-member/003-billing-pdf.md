---
canonical_id: family-member/003-billing-pdf
route: /dashboard/family/client/<int:client_id>/billing-pdf/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — PDF download endpoint with no rendered UI.

**Interaction notes:**
- GET this URL → with billable visits, response is a PDF (browser download). Without billable data, response body is plain text `No billing data available for this period.` (the captured state — fixture has no billable visits). View is `family_billing_pdf` (`dashboard/views.py:314`).
- Query params → `month`, `year`, `revision` select the invoice instance. View auto-generates a draft `Invoice` from billable visits if none exists.
- IDOR boundary → `FamilyPortalService.verify_access`; only family members linked to the client via `ClientFamilyMember` can render. Rate-limited 10/h per user; HIPAA-access-logged in v1.
