---
canonical_id: agency-admin/061-preview
route: /clients/<int:client_id>/schedule/preview/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "none" — HTML preview partial returned to the print-config panel; the captured WebP shows the rendered weekly calendar grid (see Interaction notes for layout detail).

**Interaction notes:**
- Endpoint → `client_schedule_preview` returns the print-config preview HTML; mirrors the schedule PDF generator's options without producing a PDF. The rendered preview shows the client identity + month header, "All times in Pacific Time" subtitle, weekly calendar grid with day numbers, and per-day cells with the assigned caregiver's chip plus "Unassigned" labels for open shifts.
- Used by → the print-config panel on [agency-admin/052-calendar](052-calendar.md); the panel re-renders this partial as the operator changes format / orientation / font / color / weekend toggles.
- Re-render workflow → follow-up GET fires with the chosen options; the operator sees the layout update inline before committing to the PDF download.
- Format options → mirror the PDF generator's args (Day / Week / Month layout, portrait / landscape, standard / large font, color / mono, weekends on / off).
- PDF download → routed through the matching schedule-PDF endpoint (out of catalog scope), which renders the same template via `reportlab` rather than the HTML preview.
