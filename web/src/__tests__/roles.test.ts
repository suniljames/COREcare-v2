import { describe, it, expect } from "vitest";
import { UserRole, hasMinRole, roleLevel } from "../lib/roles";

describe("Role hierarchy", () => {
  it("has correct privilege levels", () => {
    expect(roleLevel(UserRole.FAMILY)).toBe(0);
    expect(roleLevel(UserRole.CAREGIVER)).toBe(1);
    expect(roleLevel(UserRole.CARE_MANAGER)).toBe(2);
    expect(roleLevel(UserRole.AGENCY_ADMIN)).toBe(3);
    expect(roleLevel(UserRole.SUPER_ADMIN)).toBe(4);
  });

  it("super_admin passes any check", () => {
    expect(hasMinRole(UserRole.SUPER_ADMIN, UserRole.FAMILY)).toBe(true);
    expect(hasMinRole(UserRole.SUPER_ADMIN, UserRole.SUPER_ADMIN)).toBe(true);
  });

  it("family fails admin check", () => {
    expect(hasMinRole(UserRole.FAMILY, UserRole.AGENCY_ADMIN)).toBe(false);
  });

  it("same role passes check", () => {
    expect(hasMinRole(UserRole.CAREGIVER, UserRole.CAREGIVER)).toBe(true);
  });
});
