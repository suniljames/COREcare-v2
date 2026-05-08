import { describe, it, expect } from "vitest";
import { SEED_IDS, substitutePlaceholders } from "../crawl.ts";

// Issue #237 extends the v2_catalog_snapshot.json fixture with a
// CareManagerProfile↔Client linkage, one Expense (REJECTED), and one
// ExpenseReceipt. Three new placeholders appear in the Care Manager routes:
//
//   /care-manager/client/<int:pk>/                        → cm_client_focus
//   /care-manager/expenses/<int:expense_id>/edit/         → cm_edit_expense
//   /care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/
//                                                         → cm_serve_receipt (skipped non_html_response)
//
// SEED_IDS must resolve all three so substitutePlaceholders does not return
// `missing` entries that route the crawler back into no_seed_data.

describe("SEED_IDS — Care Manager fixture extension (#237)", () => {
  it("maps int:pk to the seeded Client pk (used by cm_client_focus)", () => {
    expect(SEED_IDS["int:pk"]).toBe(1);
  });

  it("maps int:expense_id to the seeded Expense pk (used by cm_edit_expense)", () => {
    expect(SEED_IDS["int:expense_id"]).toBe(1);
  });

  it("maps int:receipt_id to the seeded ExpenseReceipt pk (used by cm_serve_receipt)", () => {
    expect(SEED_IDS["int:receipt_id"]).toBe(1);
  });

  it("substitutes /care-manager/client/<int:pk>/ to a concrete URL", () => {
    const r = substitutePlaceholders("/care-manager/client/<int:pk>/");
    expect(r.substituted).toBe(true);
    expect(r.missing).toEqual([]);
    expect(r.url).toBe("/care-manager/client/1/");
  });

  it("substitutes /care-manager/expenses/<int:expense_id>/edit/ to a concrete URL", () => {
    const r = substitutePlaceholders("/care-manager/expenses/<int:expense_id>/edit/");
    expect(r.substituted).toBe(true);
    expect(r.missing).toEqual([]);
    expect(r.url).toBe("/care-manager/expenses/1/edit/");
  });

  it("substitutes the receipt route's two placeholders to a concrete URL", () => {
    // The receipt route itself is skipped at capture time (see
    // skip-reasons.test.ts) but substitution must still resolve so the
    // crawler doesn't double-classify the skip-reason.
    const r = substitutePlaceholders(
      "/care-manager/expenses/<int:expense_id>/receipt/<int:receipt_id>/",
    );
    expect(r.substituted).toBe(true);
    expect(r.missing).toEqual([]);
    expect(r.url).toBe("/care-manager/expenses/1/receipt/1/");
  });
});
