import { describe, it, expect } from "vitest";
import { parseArgs } from "../crawl.ts";

// parseArgs is the unit-testable kernel of CLI-flag handling. Phase 2A adds
// --resume-from, --only-personas, --only-routes for operator recovery.

describe("parseArgs", () => {
  it("requires --output-dir", () => {
    expect(() => parseArgs([], { exitOnError: false })).toThrow(/--output-dir is required/);
  });

  it("accepts --output-dir as the minimum invocation", () => {
    const args = parseArgs(["--output-dir", "/tmp/out"], { exitOnError: false });
    expect(args.outputDir).toBe("/tmp/out");
    expect(args.resumeFrom).toBeUndefined();
    expect(args.onlyPersonas).toBeUndefined();
    expect(args.onlyRoutes).toBeUndefined();
  });

  it("parses --resume-from as a single persona slug", () => {
    const args = parseArgs(
      ["--output-dir", "/tmp/out", "--resume-from", "caregiver"],
      { exitOnError: false },
    );
    expect(args.resumeFrom).toBe("caregiver");
  });

  it("parses --only-personas as a comma-separated list of slugs", () => {
    const args = parseArgs(
      ["--output-dir", "/tmp/out", "--only-personas", "super-admin,agency-admin"],
      { exitOnError: false },
    );
    expect(args.onlyPersonas).toEqual(["super-admin", "agency-admin"]);
  });

  it("parses --only-routes as a comma-separated list of canonical_ids", () => {
    const args = parseArgs(
      ["--output-dir", "/tmp/out", "--only-routes", "agency-admin/001-dashboard,caregiver/004-clock-in"],
      { exitOnError: false },
    );
    expect(args.onlyRoutes).toEqual([
      "agency-admin/001-dashboard",
      "caregiver/004-clock-in",
    ]);
  });

  it("rejects unknown flags", () => {
    expect(() => parseArgs(
      ["--output-dir", "/tmp/out", "--bogus", "x"],
      { exitOnError: false },
    )).toThrow(/unknown arg: --bogus/);
  });

  it("strips whitespace from comma-separated list values", () => {
    const args = parseArgs(
      ["--output-dir", "/tmp/out", "--only-personas", "super-admin, agency-admin , caregiver"],
      { exitOnError: false },
    );
    expect(args.onlyPersonas).toEqual(["super-admin", "agency-admin", "caregiver"]);
  });
});
