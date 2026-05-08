import { describe, it, expect } from "vitest";
import { classifyScreenshotRef } from "../crawl.ts";

// Issue #237 reclassifies cm_serve_receipt as non_html_response (the existing
// taxonomy entry — see docs/legacy/README.md "Skip-reason taxonomy"). The
// inventory's screenshot_ref column is the source of truth: when its value
// starts with "not_screenshotted:", the crawler must skip the route and
// propagate the reason verbatim into the run-manifest. Capture-classification
// is pure; this lets it be tested without spinning up Playwright.

describe("classifyScreenshotRef", () => {
  it("classifies a captured ref as 'capture'", () => {
    const r = classifyScreenshotRef("care-manager/002-client");
    expect(r.kind).toBe("capture");
  });

  it("classifies not_screenshotted: non_html_response as skipped with that reason", () => {
    const r = classifyScreenshotRef("not_screenshotted: non_html_response");
    expect(r.kind).toBe("skip");
    expect(r.reason).toBe("non_html_response");
  });

  it("classifies not_screenshotted: no_seed_data as skipped with that reason", () => {
    const r = classifyScreenshotRef("not_screenshotted: no_seed_data");
    expect(r.kind).toBe("skip");
    expect(r.reason).toBe("no_seed_data");
  });

  it("strips whitespace after the colon (operator-format leniency)", () => {
    const r = classifyScreenshotRef("not_screenshotted:   pending #79");
    expect(r.kind).toBe("skip");
    expect(r.reason).toBe("pending #79");
  });

  it("handles missing space after the colon", () => {
    const r = classifyScreenshotRef("not_screenshotted:non_html_response");
    expect(r.kind).toBe("skip");
    expect(r.reason).toBe("non_html_response");
  });

  it("does not classify other prefixes as skip", () => {
    // Defensive: only the literal "not_screenshotted:" prefix triggers skip.
    const r = classifyScreenshotRef("foo: bar");
    expect(r.kind).toBe("capture");
  });
});
