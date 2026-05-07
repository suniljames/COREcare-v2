import { describe, it, expect } from "vitest";
import { renderCaption } from "../crawl.ts";

// Phase 2A renamed `viewport` → `lead_viewport` because each caption file
// describes BOTH viewport WebPs (one per route, not one per viewport-pair).
// The lead_viewport field encodes which viewport is canonical for the
// persona — Caregiver / Family Member lead with mobile per RESPONSIVE.md;
// other personas lead with desktop.

describe("renderCaption", () => {
  const fm = {
    canonicalId: "agency-admin/001-dashboard",
    route: "/admin/todays-shifts/",
    persona: "Agency Admin",
    leadViewport: "desktop" as const,
    seedState: "populated",
    v1Commit: "9738412a6e41064203fc253d9dd2a5c6a9c2e231",
    generated: "2026-05-07",
  };

  it("starts and ends with --- frontmatter delimiters", () => {
    const out = renderCaption(fm);
    const lines = out.trimEnd().split("\n");
    expect(lines[0]).toBe("---");
    const secondDelim = lines.indexOf("---", 1);
    expect(secondDelim).toBeGreaterThan(0);
  });

  it("contains every required frontmatter field, including lead_viewport", () => {
    const out = renderCaption(fm);
    expect(out).toContain("canonical_id: agency-admin/001-dashboard");
    expect(out).toContain("route: /admin/todays-shifts/");
    expect(out).toContain("persona: Agency Admin");
    expect(out).toContain("lead_viewport: desktop");
    expect(out).toContain("seed_state: populated");
    expect(out).toContain("v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231");
    expect(out).toContain("generated: 2026-05-07");
  });

  it("does NOT emit the deprecated `viewport:` field", () => {
    // The Phase 1 schema used `viewport: desktop|mobile`; Phase 2A renames it.
    const out = renderCaption(fm);
    expect(out).not.toMatch(/^viewport:/m);
  });

  it("includes the TODO marker for the body", () => {
    const out = renderCaption(fm);
    expect(out).toContain("<!-- TODO: author CTAs + interaction notes per CAPTION-STYLE.md (Phase 3) -->");
  });

  it("frontmatter canonical_id matches the file path the caller will use", () => {
    const out = renderCaption(fm);
    const match = out.match(/canonical_id:\s*(\S+)/);
    expect(match).not.toBeNull();
    expect(match?.[1]).toBe("agency-admin/001-dashboard");
  });

  it("renders mobile lead_viewport correctly", () => {
    const mobile = { ...fm, leadViewport: "mobile" as const };
    expect(renderCaption(mobile)).toContain("lead_viewport: mobile");
  });

  it("preserves canonical persona names with spaces", () => {
    const cm = { ...fm, persona: "Care Manager" };
    expect(renderCaption(cm)).toContain("persona: Care Manager");

    const fm2 = { ...fm, persona: "Family Member" };
    expect(renderCaption(fm2)).toContain("persona: Family Member");
  });
});

// leadViewportFor: pure helper that picks the canonical lead viewport for
// a given persona slug. Caregiver + Family Member lead mobile; everyone
// else leads desktop. Phase 2A.
import { leadViewportFor } from "../crawl.ts";

describe("leadViewportFor", () => {
  it("returns 'mobile' for caregiver and family-member", () => {
    expect(leadViewportFor("caregiver")).toBe("mobile");
    expect(leadViewportFor("family-member")).toBe("mobile");
  });

  it("returns 'desktop' for super-admin, agency-admin, care-manager, client", () => {
    expect(leadViewportFor("super-admin")).toBe("desktop");
    expect(leadViewportFor("agency-admin")).toBe("desktop");
    expect(leadViewportFor("care-manager")).toBe("desktop");
    expect(leadViewportFor("client")).toBe("desktop");
  });

  it("defaults to 'desktop' for unknown persona slugs", () => {
    expect(leadViewportFor("unknown-slug")).toBe("desktop");
  });
});
