import { describe, it, expect } from "vitest";

describe("Auth middleware", () => {
  it("exports a config with matcher patterns", async () => {
    const { config } = await import("../middleware");
    expect(config).toBeDefined();
    expect(config.matcher).toBeInstanceOf(Array);
    expect(config.matcher.length).toBeGreaterThan(0);
  });
});
