import { describe, expect, it } from 'vitest';

import {
  describeWorkspaceRole,
  findWorkspaceCapability,
  findWorkspacePage,
  findWorkspacePageByPath,
  gatewayIssuedRoles,
  getWorkspacePage,
  isPageInRoleScope,
  isWorkspaceCapabilitySourced,
  isWorkspaceRole,
  resolveCapabilityState,
  WORKSPACE_ALLOWED_ROLES,
  WORKSPACE_MANAGEMENT_ROLES,
  WORKSPACE_PAGE_IDS,
  WORKSPACE_PAGES,
  WORKSPACE_PROFESSIONAL_ROLES,
  WORKSPACE_ROLE_DESCRIPTORS,
  workspaceNavigationForRole,
  workspaceNavigationGroups,
  workspacePageHref,
  workspacePagesForRole,
} from './registry';

/** The design document's page map, in the order it lists them. */
const DOCUMENTED_PATHS = [
  'overview',
  'assignments',
  'cases',
  'knowledge',
  'reports',
  'team',
  'approvals',
  'targets',
  'audit',
  'operations',
  'operations/jobs',
  'operations/events',
  'operations/health',
  'settings',
  'settings/notifications',
  'settings/access',
];

const MESSAGE_KEY = /^[a-zA-Z][a-zA-Z0-9]*(\.[a-zA-Z][a-zA-Z0-9]*)+$/;

describe('workspace role registry', () => {
  it('admits the current management roles and the registered professional roles', () => {
    expect([...WORKSPACE_MANAGEMENT_ROLES]).toEqual([
      'admin',
      'security_admin',
      'content_admin',
      'user_admin',
    ]);
    expect([...WORKSPACE_PROFESSIONAL_ROLES]).toEqual([
      'advisor',
      'operator',
      'support',
      'analyst',
      'content_editor',
      'auditor',
      'manager',
    ]);
    expect(WORKSPACE_ALLOWED_ROLES).toHaveLength(11);
  });

  it('denies every consumer and platform role by default', () => {
    for (const role of [
      'regular',
      'tourist',
      'farmer',
      'researcher',
      'organization',
      'guest',
      '',
    ]) {
      expect(isWorkspaceRole(role)).toBe(false);
    }
    expect(isWorkspaceRole('admin')).toBe(true);
    expect(isWorkspaceRole(null)).toBe(false);
    expect(isWorkspaceRole(undefined)).toBe(false);
  });

  it('describes every allowlisted role without granting it', () => {
    for (const role of WORKSPACE_ALLOWED_ROLES) {
      const descriptor = describeWorkspaceRole(role);
      expect(descriptor.inAllowlist).toBe(true);
      expect(descriptor.id).toBe(role);
    }
    const unknown = describeWorkspaceRole('root');
    expect(unknown.inAllowlist).toBe(false);
    expect(unknown.issuedByGateway).toBe(false);
    expect(unknown.labelKey).toBeNull();
  });

  it('marks a professional role the gateway does not mint as unissued', () => {
    // The gateway role constants are farmer, advisor and the four admin roles.
    expect([...gatewayIssuedRoles()].sort()).toEqual(
      ['advisor', 'admin', 'content_admin', 'security_admin', 'user_admin'].sort(),
    );
    for (const descriptor of WORKSPACE_ROLE_DESCRIPTORS) {
      if (descriptor.issuedByGateway) expect(descriptor.labelKey).not.toBeNull();
    }
    expect(describeWorkspaceRole('analyst').issuedByGateway).toBe(false);
    expect(describeWorkspaceRole('auditor').issuedByGateway).toBe(false);
  });

  it('keeps every role descriptor unique and inside the allowlist', () => {
    const ids = WORKSPACE_ROLE_DESCRIPTORS.map((descriptor) => descriptor.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const id of ids) expect(WORKSPACE_ALLOWED_ROLES).toContain(id);
  });
});

describe('workspace page registry', () => {
  it('covers every documented path exactly once', () => {
    expect(WORKSPACE_PAGES.map((page) => page.path)).toEqual(DOCUMENTED_PATHS);
    expect(new Set(WORKSPACE_PAGE_IDS).size).toBe(DOCUMENTED_PATHS.length);
    for (const path of DOCUMENTED_PATHS) {
      expect(findWorkspacePageByPath(path)).toBeDefined();
    }
  });

  it('keeps every label, lead and capability label on an existing message key', () => {
    for (const page of WORKSPACE_PAGES) {
      expect(page.labelKey).toMatch(MESSAGE_KEY);
      expect(page.leadKey).toMatch(MESSAGE_KEY);
      expect(page.capabilities.length).toBeGreaterThan(0);
      for (const capability of page.capabilities) {
        expect(capability.labelKey).toMatch(MESSAGE_KEY);
        expect(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']).toContain(capability.method);
      }
    }
  });

  it('binds only endpoints the gateway or the BFF really registers', () => {
    for (const page of WORKSPACE_PAGES) {
      for (const capability of page.capabilities) {
        if (capability.endpoint === null) {
          expect(capability.gap).not.toBe('');
          continue;
        }
        expect(capability.gap).toBe('');
        expect(
          capability.endpoint.startsWith('/api/v1/') ||
            capability.endpoint.startsWith('/api/auth/'),
        ).toBe(true);
        if (capability.endpoint.startsWith('/api/auth/')) {
          expect(capability.endpointKind).toBe('bff');
        }
      }
    }
  });

  it('never reports a capability without a source as available', () => {
    const assignments = getWorkspacePage('assignments');
    for (const capability of assignments.capabilities) {
      expect(isWorkspaceCapabilitySourced(capability)).toBe(false);
      expect(resolveCapabilityState(capability, true)).toBe('unavailable');
    }
    const health = getWorkspacePage('operations-health');
    for (const capability of health.capabilities) {
      expect(resolveCapabilityState(capability, true)).toBe('available');
      expect(resolveCapabilityState(capability, false)).toBe('unavailable');
    }
  });

  it('keeps MFA, export and customer data unavailable', () => {
    const access = getWorkspacePage('settings-access');
    expect(findWorkspaceCapability(access, 'mfa-state')?.endpoint).toBeNull();

    const reports = getWorkspacePage('reports');
    expect(findWorkspaceCapability(reports, 'report-export')?.endpoint).toBeNull();

    const audit = getWorkspacePage('audit');
    expect(findWorkspaceCapability(audit, 'audit-export')?.endpoint).toBeNull();
    // The only audit source is restricted to a non-personal projection and the
    // page discloses that the upstream route applies no role gate.
    const events = findWorkspaceCapability(audit, 'audit-events');
    expect(events?.endpoint).not.toBeNull();
    expect(events?.projection).toBe('non-personal');
    expect(events?.upstreamRoles).toBeNull();
  });

  it('keeps notification preferences unavailable while the payload is fixed', () => {
    const notifications = getWorkspacePage('settings-notifications');
    for (const capability of notifications.capabilities) {
      expect(isWorkspaceCapabilitySourced(capability)).toBe(false);
    }
  });

  it('resolves pages by id and refuses an unregistered id', () => {
    expect(getWorkspacePage('overview').path).toBe('overview');
    expect(findWorkspacePage('overview')?.id).toBe('overview');
    expect(findWorkspacePage('billing')).toBeUndefined();
    expect(() => getWorkspacePage('billing' as 'overview')).toThrow(/not registered/);
  });

  it('builds locale-aware hrefs and never invents an intermediate page', () => {
    expect(workspacePageHref('fa', '')).toBe('/fa/workspace');
    expect(workspacePageHref('en', 'operations/health')).toBe('/en/workspace/operations/health');
  });
});

describe('workspace navigation', () => {
  it('groups every page exactly once, in the documented order', () => {
    const groups = workspaceNavigationGroups();
    expect(groups.map((group) => group.id)).toEqual([
      'work',
      'governance',
      'operations',
      'settings',
    ]);
    const flattened = groups.flatMap((group) => group.pages.map((page) => page.path));
    expect(flattened).toEqual(DOCUMENTED_PATHS);
  });

  it('filters navigation by role without ever granting access', () => {
    const advisor = workspaceNavigationForRole('advisor');
    const advisorPaths = advisor.flatMap((group) => group.pages.map((page) => page.path));
    expect(advisorPaths).toContain('assignments');
    expect(advisorPaths).toContain('knowledge');
    // Governance and operations scopes belong to other professional roles.
    expect(advisorPaths).not.toContain('audit');
    expect(advisorPaths).not.toContain('operations/health');
  });

  it('shows a management role every documented surface', () => {
    const paths = workspacePagesForRole('admin').map((page) => page.path);
    expect(paths).toEqual(DOCUMENTED_PATHS);
  });

  it('returns an empty navigation for a role outside the allowlist', () => {
    for (const role of ['regular', 'farmer', 'researcher', null, undefined, '']) {
      expect(workspaceNavigationForRole(role)).toEqual([]);
      expect(workspacePagesForRole(role)).toEqual([]);
    }
  });

  it('reports a descriptive scope without turning it into a gate', () => {
    const audit = getWorkspacePage('audit');
    expect(isPageInRoleScope(audit, 'auditor')).toBe(true);
    expect(isPageInRoleScope(audit, 'admin')).toBe(true);
    expect(isPageInRoleScope(audit, 'advisor')).toBe(false);
    expect(isPageInRoleScope(audit, 'farmer')).toBe(false);
    expect(isPageInRoleScope(audit, null)).toBe(false);
  });
});
