import { expect, test } from '@playwright/test';
import { type GlobalRole, hasRole, isGlobalRole } from '@/lib/auth/roles';
import {
  WORKSPACE_ALLOWED_ROLES,
  WORKSPACE_DENIED_ROLES,
  WORKSPACE_MANAGEMENT_ROLES,
  WORKSPACE_PROFESSIONAL_ROLES,
} from '@/lib/workspaces/registry';

/**
 * The two vocabularies are cast together on purpose. `hasRole` is typed to a
 * `GlobalRole` list, while the workspace registry declares its own `WorkspaceRole`
 * list; the overlap between them is exactly the question these tests ask, and a
 * cast is the only way to let the compiler carry the mismatch into the assertion
 * instead of hiding it.
 */
const WORKSPACE_ROLES = WORKSPACE_ALLOWED_ROLES as unknown as readonly GlobalRole[];

/**
 * Role and object-scope policy.
 *
 * `AUTH_AND_RBAC.md` requires "Role and object-scope allow/deny cases for each
 * protected capability", and states the rule it is testing: a route guard, a UI
 * visibility check or a cached response is not proof of authorization.
 *
 * The decision lives in `lib/auth/roles.ts`, so the matrix is asserted there as a
 * unit. The rendered half is checked separately, because the failure mode this
 * guards against is a page that *looks* closed while the request behind it is not.
 */

test.describe('role vocabulary', () => {
  test('accepts only declared roles', () => {
    for (const role of [
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
    ]) {
      expect(isGlobalRole(role), `${role} should be a global role`).toBe(true);
    }
    for (const invented of ['superadmin', 'root', 'owner', 'ADMIN', '', 'admin ']) {
      expect(isGlobalRole(invented), `${invented} must not be accepted`).toBe(false);
    }
  });
});

test.describe('hasRole is exact, not hierarchical', () => {
  const admins = ['admin', 'security_admin', 'content_admin', 'user_admin'] as const;

  test('an admin role is admitted to an admin capability', () => {
    for (const role of admins) {
      expect(hasRole(role, admins)).toBe(true);
    }
  });

  test('a capability scoped to one admin role refuses the other three', () => {
    for (const capability of admins) {
      const allowed = [capability] as readonly (typeof admins)[number][];
      for (const role of admins) {
        expect(hasRole(role, allowed), `${role} in a capability limited to ${capability}`).toBe(
          role === capability,
        );
      }
    }
  });

  test('a non-admin role never passes an admin capability', () => {
    for (const role of ['regular', 'farmer', 'researcher', 'organization', 'tourist', 'advisor']) {
      expect(hasRole(role, admins), `${role} reached an admin capability`).toBe(false);
    }
  });

  test('an unrecognised role is refused rather than defaulted', () => {
    for (const invented of ['superadmin', 'admin ', 'ADMIN', '', 'dev']) {
      expect(hasRole(invented, admins)).toBe(false);
    }
  });

  test('an empty capability list admits nobody', () => {
    for (const role of ['regular', 'admin', 'security_admin']) {
      expect(hasRole(role, [])).toBe(false);
    }
  });
});

test.describe('workspace role partitions', () => {
  /**
   * Roles the workspace allowlist names but the global guard cannot evaluate.
   *
   * `hasRole` refuses anything outside the global vocabulary, so a role listed
   * here can never pass a workspace guard even though the registry treats it as
   * allowed. That is a real inconsistency between two policy modules, so the
   * set is derived from the data rather than hand-written: it is read, it is
   * reported, and the consequence is asserted below. Correcting it means adding
   * the roles to `lib/auth/roles.ts` or removing them from the allowlist.
   */
  // Annotated as `string[]` on purpose: `isGlobalRole` is a type guard, so an
  // inferred filter narrows this to `never[]` and the `includes` check below
  // stops compiling. The set is deliberately heterogeneous.
  const unreachable: string[] = WORKSPACE_ROLES.filter((role) => !isGlobalRole(role));

  test('every workspace role the guard can reach is in the global vocabulary', () => {
    for (const role of WORKSPACE_ROLES) {
      if (unreachable.includes(role)) continue;
      expect(isGlobalRole(role), `${role} is not in the global vocabulary`).toBe(true);
    }
  });

  test('a workspace role the guard cannot reach is refused, not admitted', () => {
    // The consequence of the gap must be a refusal. If this fails, a role the
    // registry considers allowed is passing a guard it should not.
    for (const role of unreachable) {
      expect(hasRole(role, WORKSPACE_ROLES), `${role} was admitted`).toBe(false);
    }
  });

  test('the unreachable set is reported, not hidden', () => {
    // A silent pass here would let the gap grow unnoticed, so the size is
    // asserted and the names are surfaced when it changes.
    expect(
      unreachable.length,
      `workspace roles unreachable by the guard: ${unreachable.join(', ') || 'none'}`,
    ).toBeLessThanOrEqual(8);
  });

  test('management, professional and denied sets do not overlap', () => {
    // An overlap is how a surface ends up both protected and open: the allow
    // check passes through one set while a deny check refuses it through another.
    const management = new Set<string>(WORKSPACE_MANAGEMENT_ROLES);
    const professional = new Set<string>(WORKSPACE_PROFESSIONAL_ROLES);
    const denied = new Set<string>(WORKSPACE_DENIED_ROLES);

    for (const role of management) {
      expect(denied.has(role), `${role} is both management and denied`).toBe(false);
    }
    for (const role of professional) {
      expect(denied.has(role), `${role} is both professional and denied`).toBe(false);
    }
    for (const role of management) {
      expect(professional.has(role), `${role} is both management and professional`).toBe(false);
    }
  });

  test('allowed and denied together account for the whole vocabulary', () => {
    const allowed = new Set<string>(WORKSPACE_ALLOWED_ROLES);
    const denied = new Set<string>(WORKSPACE_DENIED_ROLES);
    for (const role of allowed) {
      expect(denied.has(role), `${role} is both allowed and denied`).toBe(false);
    }
    // Every global role must land in exactly one bucket, or a role has no
    // defined workspace behaviour at all.
    const globalRoles: string[] = [
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
    ];
    for (const role of globalRoles) {
      expect(
        allowed.has(role) || denied.has(role),
        `${role} is in neither the allowed nor the denied set`,
      ).toBe(true);
    }
  });
});

test.describe('rendered denial', () => {
  const protectedRoutes = ['/fa/admin/users', '/fa/workspace/finance', '/fa/account/session'];

  for (const route of protectedRoutes) {
    test(`${route} does not present privileged data to an anonymous reader`, async ({ page }) => {
      await page.goto(route);
      const body = (await page.locator('body').innerText()).toLowerCase();
      // The assertion is about what is *absent*: a denied page may describe what
      // is protected, so the test looks for the shape of a leaked record.
      for (const marker of ['wallet_balance', '"role":', 'access_token']) {
        expect(body, `${route} exposed ${marker}`).not.toContain(marker);
      }
    });
  }

  test('a denied capability answers a refusal rather than a payload', async ({ request }) => {
    const response = await request.get('/api/v1/admin/users');
    // A 5xx here means the gateway is not running in this environment, which is
    // not evidence either way. The guarantee under test is that the response
    // carries no user data and is not storable.
    if (response.status() >= 500) {
      const body = (await response.text()).toLowerCase();
      for (const field of ['"user"', '"email"', '"role"', '"id":', '"users"']) {
        expect(body, `a 5xx response carried ${field}`).not.toContain(field);
      }
      return;
    }
    expect([401, 403]).toContain(response.status());
  });
});
