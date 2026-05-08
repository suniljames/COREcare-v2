---
canonical_id: agency-admin/054-create
route: /clients/<int:client_id>/events/create/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Back to Calendar" link, "Add New Event" header, "Event Title *" input, "Event Type *" select (default "Other"), "Start Date *" + "Start Time *", "End Date *" + "End Time *", "Location" input, "Notes" textarea, "Create Event" green button, "Cancel" outline button, "Home" / "Schedule" / "Earnings" / "Profile" bottom-nav, "Accessibility" footer link.

**Interaction notes:**
- Page load → `create_event` (`clients/event_form.html`) renders the form for a custom non-shift calendar event (medical appointment, milestone, family note) on a client's calendar.
- "Create Event" → ⚠ destructive: POSTs the form to create a `CalendarEvent` row scoped to the client; redirects to [agency-admin/052-calendar](052-calendar.md) with a success flash. Skipped by crawler.
- "Cancel" → returns to [agency-admin/052-calendar](052-calendar.md) without saving.
- "Event Type" select → constrains the event category for downstream filters (medical, milestone, family-note, other).
- "Back to Calendar" → returns to the per-client calendar.
- Edit variant → re-uses this form template at `/clients/<int:client_id>/events/<int:event_id>/edit/` (out of catalog scope), pre-filled with the event's current values + an attachment list with delete controls.
