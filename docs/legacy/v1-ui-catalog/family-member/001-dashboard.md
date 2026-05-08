---
canonical_id: family-member/001-dashboard
route: /family/dashboard/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — captured page is a Django `DEBUG=True` 404.

**Interaction notes:**
- GET `/family/dashboard/` → 404. ⚠ inventory mismatch: `dashboard.urls` is included under `/dashboard/` (`elitecare/urls.py:186`), so `family_dashboard` (`dashboard/views.py:159`) actually lives at `/dashboard/family/dashboard/`. A `RedirectView` at `/family/` (`elitecare/urls.py:57–59`) reaches the named pattern.
- GET the real URL → renders one card per `ClientFamilyMember` link for `request.effective_user`, with quick links into [family-member/002-client](002-client.md). `effective_user` so View-As sessions render the impersonated user's links. v1 has no audit on this route.
