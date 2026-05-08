---
canonical_id: agency-admin/052-calendar
route: /clients/<int:client_id>/calendar/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Back to My Clients" link, "Calendar & Schedule" header with client name, "Day" / "Week" / "Month" view toggle, "Previous" / "Today" / "Next" date paginator, "Download PDF" green CTA, "Undo" snackbar (briefly visible), per-day "SHIFT" rows with assigned-caregiver chips, "Edit Shift" outline button per shift card, "No events scheduled" empty rows, "Home" / "Schedule" / "Earnings" / "Profile" bottom-nav, "Logout" header link.

**Interaction notes:**
- Page load → `client_calendar` (`clients/client_calendar.html`) renders the unified per-client calendar combining scheduled shifts and custom events; daily, weekly, and monthly views supported.
- "Day" / "Week" / "Month" → switches the view mode (GET); monthly adds DST transition annotations per the inventory entry.
- "Previous" / "Today" / "Next" → step the visible date range (GET).
- "Download PDF" → renders the schedule PDF via `reportlab`; the print-config preview at [agency-admin/061-preview](061-preview.md) mirrors the same options.
- "Edit Shift" per row → drills to the shift edit form (out of catalog scope); ⚠ destructive when the form posts.
- Per-day rows → backed by [agency-admin/053-api](053-api.md), which serves the shifts + events feed asynchronously.
- "+ New Event" workflow → enters [agency-admin/054-create](054-create.md) for non-shift calendar events (medical appointments, milestones, family notes).
- "Undo" snackbar → surfaces briefly after the user moves or deletes a shift; clicking restores the prior state via a follow-up POST.
