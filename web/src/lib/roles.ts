/**
 * Role hierarchy and permission utilities.
 * Mirrors the backend ROLE_HIERARCHY in app/rbac.py.
 */

export const UserRole = {
  FAMILY: "family",
  CAREGIVER: "caregiver",
  CARE_MANAGER: "care_manager",
  AGENCY_ADMIN: "agency_admin",
  SUPER_ADMIN: "super_admin",
} as const;

export type UserRoleType = (typeof UserRole)[keyof typeof UserRole];

const ROLE_HIERARCHY: UserRoleType[] = [
  UserRole.FAMILY,
  UserRole.CAREGIVER,
  UserRole.CARE_MANAGER,
  UserRole.AGENCY_ADMIN,
  UserRole.SUPER_ADMIN,
];

export function roleLevel(role: UserRoleType): number {
  return ROLE_HIERARCHY.indexOf(role);
}

export function hasMinRole(userRole: UserRoleType, minRole: UserRoleType): boolean {
  return roleLevel(userRole) >= roleLevel(minRole);
}
