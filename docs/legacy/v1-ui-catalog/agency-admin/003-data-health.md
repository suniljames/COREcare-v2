---
canonical_id: agency-admin/003-data-health
route: /admin/data-health/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Data Health Report" header with "Verified" date, "TOTAL RECORDS IN ..." stat card, "Core Entities" expandable section, "Logout" header link.

**Interaction notes:**
- Page load → `data_health_view` (`admin/data_health.html`) reports v1 data integrity counts (orphan records, stale flags, schedule gaps) across major models.
- "Verified" timestamp → marks when the integrity audit last ran.
- "Core Entities" section → groups counts and flagged-record lists by model; each row drills to the affected record so an admin can fix it.
- Role usage → operational health-check landing for the Agency Admin; surfaces v1 schedule + chart gaps that the v2 migration must reconcile.

