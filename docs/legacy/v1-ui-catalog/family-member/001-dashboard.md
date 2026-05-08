---
canonical_id: family-member/001-dashboard
route: /dashboard/family/dashboard/
persona: Family Member
lead_viewport: mobile
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Log out", "View Details", "Back to Home".

**Interaction notes:**
- "View Details" → navigates to [family-member/002-client](002-client.md) (the per-client family portal). Captured fixture has 1 linked client; one card renders per `ClientFamilyMember` link for `request.effective_user`.
- "Back to Home" → navigates to the role-aware home target.
- "Log out" → ends the session and redirects to the login page.
- Page load → `family_dashboard` view (`dashboard/views.py:159`) hydrates `links = ClientFamilyMember.objects.filter(user=user).select_related("client")`. `effective_user` is used so View-As sessions render the impersonated user's links rather than the admin's. v1 has no audit on this route — v2 design must add (per inventory).
