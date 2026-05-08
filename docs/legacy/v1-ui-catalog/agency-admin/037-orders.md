---
canonical_id: agency-admin/037-orders
route: /charting/medications/<int:client_id>/orders/
persona: Agency Admin
lead_viewport: desktop
seed_state: populated
v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231
generated: 2026-05-08
---
**CTAs visible:** "Home" breadcrumb, "Medication Orders" header with client name, "Active Orders" tab, "No active medication orders for this client." empty-state copy, "Logout" header link.

**Interaction notes:**
- Page load → `medication_orders_list` (`charting/medication_orders.html`) lists the client's active medication orders with dose, route, frequency, start date, and prescriber.
- "Active Orders" tab → currently the only state shown; the populated render adds an "Inactive" tab gated on a `?status=inactive` query.
- Per-order row drill-in → opens the single-order detail (out of catalog scope).
- Empty state → fixture has no active orders for the client; populated render renders one row per order with the prescriber's name and a refill / discontinue per-row action.
- Permissions → guarded by Django's `@staff_member_required` decorator; the v1 view does not apply a finer-grained capability check.
