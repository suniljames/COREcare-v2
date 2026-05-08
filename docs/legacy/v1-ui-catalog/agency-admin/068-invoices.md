---
canonical_id: agency-admin/068-invoices
route: /dashboard/admin/invoices/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Back to Dashboard" link, "Client Invoices" header, "QuickBooks Not Connected" warning panel with "Connect QuickBooks" link, "Weekly Billing Summary (Mon-Sun)" header, "+ Add Reimbursement" green button, "Previous" / "Next" week paginator, "Week (Mon-Sun)" range label, "No billable activity this week." empty state, "Filter by client:" select (default "All Clients"), "Logout" header link.

**Interaction notes:**
- Page load → `admin_client_invoices` (`dashboard/admin_client_invoices.html`) lists all client invoices, allows uploading new invoice PDFs, and shows the automated weekly billing summary; supports adding standalone reimbursements.
- "QuickBooks Not Connected" warning → links to [agency-admin/075-connect](075-connect.md); the v1 fixture has no active QuickBooks connection at crawl time.
- "+ Add Reimbursement" → ⚠ destructive: opens an inline form to create a `Reimbursement` row attached to a client / period; submit fires a POST. Skipped by crawler.
- "Previous" / "Next" → step the visible Mon–Sun window (GET).
- "Filter by client:" select → narrows the rendered invoices + reimbursements to a single client (GET).
- Per-invoice email CTA → drills to [agency-admin/071-email](071-email.md) keyed on the client id.
- Per-invoice delete → POSTs to `/dashboard/admin/invoices/<int:invoice_id>/delete/` (out of catalog scope) and ⚠ destructive (deletes the row + attached PDF).
- Send-to-QuickBooks → drills to [agency-admin/079-send-invoice](079-send-invoice.md) when the connection is active.
