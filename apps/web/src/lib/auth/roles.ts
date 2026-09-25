const globalRoles = [
  'regular',
  'tourist',
  'farmer',
  'advisor',
  'researcher',
  'organization',
  'admin',
  'security_admin',
  'content_admin',
  'user_admin',
] as const;

export type GlobalRole = (typeof globalRoles)[number];

export function isGlobalRole(role: string): role is GlobalRole {
  return globalRoles.includes(role as GlobalRole);
}

export function hasRole(role: string, allowed: readonly GlobalRole[]): boolean {
  return isGlobalRole(role) && allowed.includes(role as GlobalRole);
}
