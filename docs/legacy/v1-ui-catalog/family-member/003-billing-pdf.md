---
canonical_id: family-member/003-billing-pdf
route: /family/client/<int:client_id>/billing-pdf/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — captured page is a Django `DEBUG=True` 404.

**Interaction notes:**
- GET `/family/client/<int:client_id>/billing-pdf/` → 404. ⚠ inventory mismatch: real path is `/dashboard/family/client/<int:client_id>/billing-pdf/` per `dashboard/urls.py:21`. View is `family_billing_pdf` (`dashboard/views.py:314`).
- GET the real URL → returns a PDF (browser initiates download) for the requested client + month. Auto-generates a draft `Invoice` from billable visits if none exists. Query params (`month`, `year`, `revision`) select the invoice instance. Rate-limited 10/h per user. HIPAA-access-logged in v1.
- IDOR boundary → `FamilyPortalService.verify_access`; only family members linked to the client via `ClientFamilyMember` can render.
