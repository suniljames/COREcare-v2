import { describe, it, expect, beforeEach, afterEach } from "vitest";

// We re-import personas.config inside each test after mutating env vars.
// vitest module cache is busted via vi.resetModules.
import { vi } from "vitest";

const PERSONA_ENVS = [
  "V1_SUPER_ADMIN_USERNAME", "V1_SUPER_ADMIN_PASSWORD",
  "V1_AGENCY_ADMIN_USERNAME", "V1_AGENCY_ADMIN_PASSWORD",
  "V1_CARE_MANAGER_USERNAME", "V1_CARE_MANAGER_PASSWORD",
  "V1_CAREGIVER_USERNAME", "V1_CAREGIVER_PASSWORD",
  "V1_FAMILY_MEMBER_USERNAME", "V1_FAMILY_MEMBER_PASSWORD",
];

describe("personas.config", () => {
  const originalEnv: Record<string, string | undefined> = {};

  beforeEach(() => {
    PERSONA_ENVS.forEach((k) => {
      originalEnv[k] = process.env[k];
      delete process.env[k];
    });
    vi.resetModules();
  });

  afterEach(() => {
    PERSONA_ENVS.forEach((k) => {
      if (originalEnv[k] === undefined) delete process.env[k];
      else process.env[k] = originalEnv[k];
    });
  });

  it("PERSONAS exposes 5 entries (Client persona excluded — no v1 portal)", async () => {
    const mod = await import("../personas.config.ts");
    expect(mod.PERSONAS).toHaveLength(5);
    const slugs = mod.PERSONAS.map((p) => p.slug);
    expect(slugs).toEqual([
      "super-admin",
      "agency-admin",
      "care-manager",
      "caregiver",
      "family-member",
    ]);
  });

  it("canonical names match the locked vocabulary", async () => {
    const mod = await import("../personas.config.ts");
    const canonicals = mod.PERSONAS.map((p) => p.canonical);
    expect(canonicals).toEqual([
      "Super-Admin",
      "Agency Admin",
      "Care Manager",
      "Caregiver",
      "Family Member",
    ]);
  });

  it("ACTIVE_PERSONAS is empty when no env vars are set", async () => {
    const mod = await import("../personas.config.ts");
    expect(mod.ACTIVE_PERSONAS).toHaveLength(0);
    expect(mod.SKIPPED_PERSONAS).toHaveLength(5);
  });

  it("ACTIVE_PERSONAS includes a persona only when both username + password are set", async () => {
    process.env.V1_CAREGIVER_USERNAME = "caregiver1@test.com";
    process.env.V1_CAREGIVER_PASSWORD = "TestCare123!";
    // Username only — should NOT be active
    process.env.V1_AGENCY_ADMIN_USERNAME = "admin@test.com";

    const mod = await import("../personas.config.ts");
    expect(mod.ACTIVE_PERSONAS).toHaveLength(1);
    expect(mod.ACTIVE_PERSONAS[0].slug).toBe("caregiver");
    expect(mod.SKIPPED_PERSONAS.map((p) => p.slug)).toContain("agency-admin");
  });

  it("treats empty-string env vars as unset", async () => {
    process.env.V1_CAREGIVER_USERNAME = "";
    process.env.V1_CAREGIVER_PASSWORD = "";
    const mod = await import("../personas.config.ts");
    expect(mod.ACTIVE_PERSONAS).toHaveLength(0);
  });
});
