import { describe, it, expect } from "vitest";
import {
  applyPersonaFilters,
  applyRouteFilter,
  deriveRouteSlug,
  type CliArgs,
  type InventoryRow,
} from "../crawl.ts";
import type { Persona } from "../personas.config.ts";

const PERSONAS: Persona[] = [
  { slug: "super-admin",   canonical: "Super-Admin",   username: "u1", password: "p1" },
  { slug: "agency-admin",  canonical: "Agency Admin",  username: "u2", password: "p2" },
  { slug: "care-manager",  canonical: "Care Manager",  username: "u3", password: "p3" },
  { slug: "caregiver",     canonical: "Caregiver",     username: "u4", password: "p4" },
  { slug: "family-member", canonical: "Family Member", username: "u5", password: "p5" },
];

const ROWS: InventoryRow[] = [
  { persona: "Agency Admin", route: "/admin/clients/",                 screenshot_ref: "" },
  { persona: "Agency Admin", route: "/admin/clients/<id>/chart/",      screenshot_ref: "" },
  { persona: "Agency Admin", route: "/admin/clients/<id>/chart/notes/", screenshot_ref: "" },
  { persona: "Agency Admin", route: "/admin/dashboard/",               screenshot_ref: "" },
  { persona: "Agency Admin", route: "/admin/billing/",                 screenshot_ref: "" },
];

const baseCli = (overrides: Partial<CliArgs> = {}): CliArgs => ({
  outputDir: "/tmp/out",
  ...overrides,
});

describe("applyPersonaFilters", () => {
  it("returns all personas when no filters set", () => {
    const out = applyPersonaFilters(PERSONAS, baseCli());
    expect(out).toHaveLength(PERSONAS.length);
    expect(out.map((p) => p.slug)).toEqual(PERSONAS.map((p) => p.slug));
  });

  it("onlyPersonas restricts to the named slugs, preserving order", () => {
    const out = applyPersonaFilters(PERSONAS, baseCli({ onlyPersonas: ["caregiver", "agency-admin"] }));
    expect(out.map((p) => p.slug)).toEqual(["agency-admin", "caregiver"]);
  });

  it("resumeFrom slices starting at the matching slug", () => {
    const out = applyPersonaFilters(PERSONAS, baseCli({ resumeFrom: "caregiver" }));
    expect(out.map((p) => p.slug)).toEqual(["caregiver", "family-member"]);
  });

  it("resumeFrom not found is a no-op (returns full list)", () => {
    const out = applyPersonaFilters(PERSONAS, baseCli({ resumeFrom: "client" }));
    expect(out.map((p) => p.slug)).toEqual(PERSONAS.map((p) => p.slug));
  });

  it("resumeFrom + onlyPersonas: filter first, then resume within the filtered set", () => {
    const out = applyPersonaFilters(
      PERSONAS,
      baseCli({ onlyPersonas: ["agency-admin", "care-manager", "caregiver"], resumeFrom: "care-manager" }),
    );
    expect(out.map((p) => p.slug)).toEqual(["care-manager", "caregiver"]);
  });
});

describe("applyRouteFilter", () => {
  it("returns all rows when no filter set", () => {
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli());
    expect(out).toHaveLength(ROWS.length);
  });

  it("onlyRoutes with NNN- prefix matches the slug exactly (NNN- is stripped)", () => {
    // "001-clients" → slug "clients" → matches /admin/clients/ only
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli({
      onlyRoutes: ["agency-admin/001-clients"],
    }));
    expect(out).toHaveLength(1);
    expect(out[0].route).toBe("/admin/clients/");
  });

  it("does NOT over-match when slugs share a common suffix (regression for endsWith bug)", () => {
    // Phase 2A bug: applyRouteFilter used .endsWith(slug) which would match
    // "/admin/clients/<id>/chart/notes/" (slug "notes") against any tail.
    // Verify: "agency-admin/notes" matches ONLY the notes row.
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli({
      onlyRoutes: ["agency-admin/notes"],
    }));
    expect(out).toHaveLength(1);
    expect(out[0].route).toBe("/admin/clients/<id>/chart/notes/");
  });

  it("onlyRoutes without NNN- prefix matches by slug directly", () => {
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli({
      onlyRoutes: ["agency-admin/dashboard"],
    }));
    expect(out).toHaveLength(1);
    expect(out[0].route).toBe("/admin/dashboard/");
  });

  it("multiple canonical_ids OR together", () => {
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli({
      onlyRoutes: ["agency-admin/001-dashboard", "agency-admin/billing"],
    }));
    expect(out.map((r) => r.route).sort()).toEqual([
      "/admin/billing/",
      "/admin/dashboard/",
    ]);
  });

  it("canonical_ids targeted at OTHER personas are ignored", () => {
    // Operator passed a caregiver canonical_id; agency-admin filter should
    // get nothing (the caregiver id matches no agency-admin rows).
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli({
      onlyRoutes: ["caregiver/001-clock-in"],
    }));
    expect(out).toHaveLength(0);
  });

  it("returns empty array when onlyRoutes set but matches nothing", () => {
    const out = applyRouteFilter(ROWS, "agency-admin", baseCli({
      onlyRoutes: ["agency-admin/nonexistent-route"],
    }));
    expect(out).toHaveLength(0);
  });
});

describe("deriveRouteSlug", () => {
  it("takes the last non-placeholder segment", () => {
    expect(deriveRouteSlug("/admin/clients/<id>/chart/")).toBe("chart");
    expect(deriveRouteSlug("/admin/dashboard/")).toBe("dashboard");
  });

  it("strips trailing/leading slashes", () => {
    expect(deriveRouteSlug("/foo/bar/")).toBe("bar");
    expect(deriveRouteSlug("foo/bar")).toBe("bar");
  });

  it("returns 'root' for the bare root path", () => {
    expect(deriveRouteSlug("/")).toBe("root");
  });

  it("lowercases and replaces non-alnum with dash", () => {
    expect(deriveRouteSlug("/admin/Client_Detail/")).toBe("client-detail");
  });
});
