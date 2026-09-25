import { describe, expect, it } from 'vitest';
import type { SessionRecord } from '@/lib/session/session-cookie';
import {
  accessRole,
  authorizeWorkspace,
  resolvePageScope,
  resolveWorkspaceAccess,
  workspaceNavigationFor,
  workspaceToken,
} from './guard';
import { getWorkspacePage } from './registry';

function sessionFor(role: string, isActive = true): SessionRecord {
  return {
    version: 1,
    accessToken: 'access-token',
    refreshToken: 'refresh-token',
    user: {
      id: 'user-1',
      email: 'advisor@example.org',
      full_name: 'Session Owner',
      role,
      language: 'fa',
      phone: null,
      country: null,
      city: null,
      avatar_url: null,
      is_email_verified: true,
      is_active: isActive,
      created_at: '2026-09-25T00:00:00Z',
    },
    createdAt: 1,
    expiresAt: 2,
  };
}

describe('workspace access guard', () => {
  it('denies a missing session', () => {
    expect(resolveWorkspaceAccess(null)).toEqual({
      status: 'denied',
      reason: 'no-session',
      role: null,
    });
  });

  it('denies an inactive account even with a valid record', () => {
    expect(resolveWorkspaceAccess(sessionFor('admin', false))).toEqual({
      status: 'denied',
      reason: 'inactive-session',
      role: 'admin',
    });
  });

  it('denies a consumer role', () => {
    for (const role of ['regular', 'tourist', 'farmer', 'researcher', 'organization']) {
      expect(resolveWorkspaceAccess(sessionFor(role))).toEqual({
        status: 'denied',
        reason: 'role-not-allowlisted',
        role,
      });
    }
  });

  it('admits a management role', () => {
    const access = resolveWorkspaceAccess(sessionFor('security_admin'));
    expect(access.status).toBe('authorized');
    if (access.status !== 'authorized') return;
    expect(access.role).toBe('security_admin');
    expect(access.session.user.email).toBe('advisor@example.org');
  });

  it('admits a professional role the gateway issues', () => {
    expect(resolveWorkspaceAccess(sessionFor('advisor')).status).toBe('authorized');
  });

  it('admits a professional role the gateway does not issue yet, as a described role', () => {
    // The registry is descriptive: whether such a session can exist at all is a
    // gateway question, and the workspace only mirrors the allowlist.
    const access = resolveWorkspaceAccess(sessionFor('manager'));
    expect(access.status).toBe('authorized');
    if (access.status !== 'authorized') return;
    expect(access.role).toBe('manager');
  });

  it('never emits navigation for a denied session', () => {
    const denied = resolveWorkspaceAccess(sessionFor('farmer'));
    expect(workspaceNavigationFor(denied)).toEqual([]);
    expect(accessRole(denied)).toBe('');
    expect(workspaceToken(null)).toBe('');
  });

  it('emits role-filtered navigation for an authorized session', () => {
    const access = resolveWorkspaceAccess(sessionFor('auditor'));
    expect(accessRole(access)).toBe('auditor');
    const paths = workspaceNavigationFor(access).flatMap((group) =>
      group.pages.map((page) => page.path),
    );
    expect(paths).toContain('audit');
    expect(paths).toContain('operations/events');
    expect(paths).not.toContain('team');
  });

  it('keeps the access token on the server side only', () => {
    const access = resolveWorkspaceAccess(sessionFor('analyst'));
    if (access.status !== 'authorized') throw new Error('expected an authorized session');
    expect(workspaceToken(access.session)).toBe('access-token');
  });

  it('reports a descriptive page scope separately from the gate', () => {
    const audit = getWorkspacePage('audit');
    expect(resolvePageScope(audit, 'auditor').status).toBe('in-scope');
    expect(resolvePageScope(audit, 'advisor')).toEqual({
      status: 'outside-descriptive-scope',
      role: 'advisor',
    });
    expect(resolvePageScope(audit, null).role).toBe('');
  });
});

describe('authorizeWorkspace', () => {
  it('resolves to a denial without a stored session', async () => {
    const access = await authorizeWorkspace();
    expect(access.status).toBe('denied');
  });
});
