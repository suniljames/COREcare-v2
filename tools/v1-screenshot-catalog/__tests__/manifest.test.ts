import { describe, it, expect } from "vitest";
import { renderManifest } from "../crawl.ts";

// renderManifest is a pure function that produces the markdown body of
// RUN-MANIFEST.md. Phase 2A added operator/host/playwright_version fields
// so a forensic reader can answer "who ran this where with what tooling"
// years from now.

describe("renderManifest", () => {
  const baseArgs = {
    v1BaseUrl: "http://localhost:8000",
    v1Commit: "9738412a6e41064203fc253d9dd2a5c6a9c2e231",
    fixtureHash: "abcd1234ef567890",
    activeCanonicals: ["Super-Admin", "Caregiver"],
    skippedCanonicals: ["Agency Admin"],
    captured: 134,
    skipped: 4,
    errored: 0,
    intercepted: 12,
    startTs: "2026-05-07T12:00:00.000Z",
    endTs: "2026-05-07T12:30:00.000Z",
    operator: "suniljames",
    host: "Darwin",
    playwrightVersion: "1.49.0",
  } as const;

  it("includes every required field as a labeled line", () => {
    const md = renderManifest(baseArgs);
    expect(md).toContain("**v1 commit:** 9738412a6e41064203fc253d9dd2a5c6a9c2e231");
    expect(md).toContain("**v1 base URL:** http://localhost:8000");
    expect(md).toContain("**Started:** 2026-05-07T12:00:00.000Z");
    expect(md).toContain("**Generated:** 2026-05-07T12:30:00.000Z");
    expect(md).toContain("**Fixture sha256:** abcd1234ef567890");
  });

  it("records operator, host, and playwright_version (Phase 2A audit fields)", () => {
    const md = renderManifest(baseArgs);
    expect(md).toContain("**Operator:** suniljames");
    expect(md).toContain("**Host:** Darwin");
    expect(md).toContain("**Playwright version:** 1.49.0");
  });

  it("lists active and skipped personas", () => {
    const md = renderManifest(baseArgs);
    expect(md).toContain("**Active:** Super-Admin, Caregiver");
    expect(md).toContain("**Skipped (no credentials):** Agency Admin");
  });

  it("renders counts including non-GET intercepted", () => {
    const md = renderManifest(baseArgs);
    expect(md).toContain("Routes captured: 134");
    expect(md).toContain("Routes skipped: 4");
    expect(md).toContain("Routes errored: 0");
    expect(md).toContain("Non-GET requests intercepted: 12");
  });

  it("renders '(none)' when active or skipped lists are empty", () => {
    const md = renderManifest({ ...baseArgs, activeCanonicals: [], skippedCanonicals: [] });
    expect(md).toContain("**Active:** (none)");
    expect(md).toContain("**Skipped (no credentials):** (none)");
  });

  it("opens with a forensic-context paragraph (Writer NIT)", () => {
    const md = renderManifest(baseArgs);
    // The first non-heading line should be a paragraph that frames the
    // file's purpose for someone who lands on it cold.
    expect(md).toMatch(/This manifest documents/);
  });
});
