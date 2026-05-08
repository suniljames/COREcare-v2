import { describe, it, expect } from "vitest";
import { substitutePlaceholders, SEED_IDS } from "../crawl.ts";

// Phase 2D adds URL-pattern placeholder substitution. The crawler can no
// longer just `page.goto(args.row.route)` because Django won't match a URL
// containing literal `<int:client_id>`. The crawler substitutes known
// placeholders with concrete IDs from the v2_catalog_snapshot.json fixture.

describe("substitutePlaceholders", () => {
  it("returns the route unchanged when there are no placeholders", () => {
    const r = substitutePlaceholders("/admin/dashboard/");
    expect(r.url).toBe("/admin/dashboard/");
    expect(r.substituted).toBe(false);
    expect(r.missing).toEqual([]);
  });

  it("substitutes a single known placeholder", () => {
    const r = substitutePlaceholders("/admin/clients/<int:client_id>/");
    expect(r.url).toBe("/admin/clients/1/");
    expect(r.substituted).toBe(true);
    expect(r.missing).toEqual([]);
  });

  it("substitutes multiple known placeholders in one route", () => {
    const r = substitutePlaceholders("/admin/clients/<int:client_id>/visit/<int:user_id>/");
    expect(r.url).toBe("/admin/clients/1/visit/4/");
    expect(r.substituted).toBe(true);
  });

  it("reports missing placeholders without substituting partials", () => {
    const r = substitutePlaceholders("/admin/visits/<int:visit_id>/approve/");
    expect(r.substituted).toBe(false);
    expect(r.missing).toEqual(["int:visit_id"]);
    // URL is left in pattern form so the operator can debug
    expect(r.url).toBe("/admin/visits/<int:visit_id>/approve/");
  });

  it("handles routes with mixed known + unknown placeholders", () => {
    const r = substitutePlaceholders("/admin/clients/<int:client_id>/visits/<int:visit_id>/");
    expect(r.substituted).toBe(false);
    expect(r.missing).toEqual(["int:visit_id"]);
    expect(r.url).toBe("/admin/clients/1/visits/<int:visit_id>/");
  });

  it("treats <id> as a generic int matching the client seed", () => {
    const r = substitutePlaceholders("/<id>/edit/");
    expect(r.url).toBe("/1/edit/");
    expect(r.substituted).toBe(true);
  });

  it("accepts a custom ID map (override default SEED_IDS)", () => {
    const r = substitutePlaceholders("/admin/clients/<int:client_id>/", {
      "int:client_id": 99,
    });
    expect(r.url).toBe("/admin/clients/99/");
  });

  it("does not match across nested brackets or partial matches", () => {
    // Defensive: ensure the regex anchors to <name> form and not free text
    const r = substitutePlaceholders("/admin/<int:client_id>/x<>y/");
    expect(r.url).toBe("/admin/1/x<>y/");
    expect(r.missing).toEqual([]);
  });

  it("SEED_IDS exposes the canonical fixture mapping", () => {
    expect(SEED_IDS["int:client_id"]).toBe(1);
    expect(SEED_IDS["int:user_id"]).toBe(4);
    expect(SEED_IDS["int:caregiver_id"]).toBe(4);
    expect(SEED_IDS["id"]).toBe(1);
  });
});
