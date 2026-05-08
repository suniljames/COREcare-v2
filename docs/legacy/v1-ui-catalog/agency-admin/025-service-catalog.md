---
canonical_id: agency-admin/025-service-catalog
route: /admin/settings/service-catalog/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" / "Settings" / "Service Catalog" breadcrumb, "Service Catalog" header, billing-rule disclosure copy ("Billable add-on services that can be attached to a visit ..."), "Active (0)" / "Retired (0)" tab toggle, "No services yet. ..." empty state with "+ Add Catalog Entry" CTA, "Logout" header link.

**Interaction notes:**
- Page load → `catalog_list_view` (`admin/billing_catalogs/catalog_list.html`) lists the agency's billable service catalog entries (service name, family-facing label, base price, hourly rate, MD-order requirement, retired flag).
- "Active" / "Retired" tabs → re-render with a `?status=` query (GET); active is the default.
- "+ Add Catalog Entry" → [agency-admin/026-new](026-new.md).
- Per-entry edit → `/admin/settings/service-catalog/<int:entry_id>/edit/` (out of catalog scope, re-uses the `catalog_form_view` pattern).
- Audit copy → "Every create, edit, and retire is captured in the audit log with value before and after." surfaces as the disclosure beneath the header; this is the agency-admin's binding compliance contract for billing changes.
