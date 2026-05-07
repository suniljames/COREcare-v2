import { describe, it, expect } from "vitest";
import { renderCaption } from "../crawl.ts";

describe("renderCaption", () => {
  const fm = {
    canonicalId: "agency-admin/001-dashboard",
    route: "/admin/todays-shifts/",
    persona: "Agency Admin",
    viewport: "desktop" as const,
    seedState: "populated",
    v1Commit: "9738412a6e41064203fc253d9dd2a5c6a9c2e231",
    generated: "2026-05-07",
  };

  it("starts and ends with --- frontmatter delimiters", () => {
    const out = renderCaption(fm);
    const lines = out.trimEnd().split("\n");
    expect(lines[0]).toBe("---");
    // Find the second --- delimiter
    const secondDelim = lines.indexOf("---", 1);
    expect(secondDelim).toBeGreaterThan(0);
  });

  it("contains every required frontmatter field", () => {
    const out = renderCaption(fm);
    expect(out).toContain("canonical_id: agency-admin/001-dashboard");
    expect(out).toContain("route: /admin/todays-shifts/");
    expect(out).toContain("persona: Agency Admin");
    expect(out).toContain("viewport: desktop");
    expect(out).toContain("seed_state: populated");
    expect(out).toContain("v1_commit: 9738412a6e41064203fc253d9dd2a5c6a9c2e231");
    expect(out).toContain("generated: 2026-05-07");
  });

  it("includes the TODO marker for the body", () => {
    const out = renderCaption(fm);
    expect(out).toContain("<!-- TODO: author CTAs + interaction notes per CAPTION-STYLE.md (Phase 3) -->");
  });

  it("frontmatter canonical_id matches the file path the caller will use", () => {
    // The canonical_id is the cross-reference handle. It MUST equal
    // <persona-slug>/<file-base> exactly — coverage-check parses this.
    const out = renderCaption(fm);
    const match = out.match(/canonical_id:\s*(\S+)/);
    expect(match).not.toBeNull();
    expect(match?.[1]).toBe("agency-admin/001-dashboard");
  });

  it("renders mobile viewport correctly", () => {
    const mobile = { ...fm, viewport: "mobile" as const };
    expect(renderCaption(mobile)).toContain("viewport: mobile");
  });

  it("preserves canonical persona names with spaces", () => {
    const cm = { ...fm, persona: "Care Manager" };
    expect(renderCaption(cm)).toContain("persona: Care Manager");

    const fm2 = { ...fm, persona: "Family Member" };
    expect(renderCaption(fm2)).toContain("persona: Family Member");
  });
});
