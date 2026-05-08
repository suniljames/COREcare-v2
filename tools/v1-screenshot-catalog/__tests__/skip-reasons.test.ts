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
    expect(classifyScreenshotRef("care-manager/002-client")).toEqual({ kind: "capture" });
  });

  it("classifies not_screenshotted: non_html_response as skipped with that reason", () => {
    expect(classifyScreenshotRef("not_screenshotted: non_html_response")).toEqual({
      kind: "skip",
      reason: "non_html_response",
    });
  });

  it("classifies not_screenshotted: no_seed_data as skipped with that reason", () => {
    expect(classifyScreenshotRef("not_screenshotted: no_seed_data")).toEqual({
      kind: "skip",
      reason: "no_seed_data",
    });
  });

  it("strips whitespace after the colon (operator-format leniency)", () => {
    expect(classifyScreenshotRef("not_screenshotted:   pending #79")).toEqual({
      kind: "skip",
      reason: "pending #79",
    });
  });

  it("handles missing space after the colon", () => {
    expect(classifyScreenshotRef("not_screenshotted:non_html_response")).toEqual({
      kind: "skip",
      reason: "non_html_response",
    });
  });

  it("does not classify other prefixes as skip", () => {
    // Defensive: only the literal "not_screenshotted:" prefix triggers skip.
    expect(classifyScreenshotRef("foo: bar")).toEqual({ kind: "capture" });
  });
});
