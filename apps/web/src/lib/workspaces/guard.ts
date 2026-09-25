import { cookies } from 'next/headers';
import { type SessionRecord, sessionCookieName } from '@/lib/session/session-cookie';
import { getStoredSession } from '@/lib/session/store';
import {
  isPageInRoleScope,
  isWorkspaceRole,
  type WorkspacePage,
  type WorkspaceRole,
  workspaceNavigationForRole,
} from './registry';

/**
 * Server-side workspace boundary.
 *
 * Deny by default, exactly as the design document requires:
 *
 * 1. a missing cookie, an unreadable record or an unreachable store is "no
 *    session", never a fallback identity;
 * 2. an inactive account is denied even when the cookie is valid;
 * 3. the role must appear in the workspace allowlist, which the registry
 *    documents and the gateway session issues;
 * 4. a child page never re-implements this gate, it only reports on it.
 */

export type WorkspaceDenialReason =
  | 'no-session'
  | 'inactive-session'
  | 'role-not-allowlisted'
  | 'role-outside-page-scope';

export type WorkspaceAccess =
  | { status: 'authorized'; role: WorkspaceRole; session: SessionRecord }
  | { status: 'denied'; reason: WorkspaceDenialReason; role: string | null };

/**
 * Reads the opaque server session. Never returns a partial or synthesised
 * record: a failure anywhere resolves to `null`, which the gate treats as
 * "not authorized".
 */
export async function readWorkspaceSession(): Promise<SessionRecord | null> {
  try {
    const store = await cookies();
    const id = store.get(sessionCookieName())?.value;
    return id ? await getStoredSession(id) : null;
  } catch {
    return null;
  }
}

/**
 * The only decision the layout is allowed to make. The role always comes from
 * the gateway session; the browser never supplies one.
 */
export function resolveWorkspaceAccess(session: SessionRecord | null): WorkspaceAccess {
  if (!session) return { status: 'denied', reason: 'no-session', role: null };
  if (session.user.is_active !== true) {
    return { status: 'denied', reason: 'inactive-session', role: session.user.role };
  }
  if (!isWorkspaceRole(session.user.role)) {
    return { status: 'denied', reason: 'role-not-allowlisted', role: session.user.role };
  }
  return { status: 'authorized', role: session.user.role, session };
}

/** Reads the session and resolves access in one deny-by-default step. */
export async function authorizeWorkspace(): Promise<WorkspaceAccess> {
  return resolveWorkspaceAccess(await readWorkspaceSession());
}

/**
 * The role a page renders under. The layout has already refused an unauthorized
 * reader, so a denied access here yields an empty role and the page reports its
 * honest state instead of a scope.
 */
export function accessRole(access: WorkspaceAccess): string {
  return access.status === 'authorized' ? access.role : '';
}

/**
 * The access token used for gateway calls. It never reaches the browser: only
 * the BFF attaches it, and only to a server-side request.
 */
export function workspaceToken(session: SessionRecord | null): string {
  return session?.accessToken ?? '';
}

/**
 * Navigation for a resolved access. An unauthorized session gets an empty
 * navigation instead of a filtered one, so no link is ever rendered for a
 * reader who is not allowed in.
 */
export function workspaceNavigationFor(access: WorkspaceAccess) {
  return access.status === 'authorized' ? workspaceNavigationForRole(access.role) : [];
}

/**
 * Descriptive scope report for a page. A reader outside the page's documented
 * professional scope is told so, and the page still renders its honest state;
 * the registry never becomes a second, frontend-only authorization gate.
 */
export function resolvePageScope(
  page: WorkspacePage,
  role: string | null | undefined,
): { status: 'in-scope' | 'outside-descriptive-scope'; role: string } {
  return {
    status: isPageInRoleScope(page, role) ? 'in-scope' : 'outside-descriptive-scope',
    role: typeof role === 'string' ? role : '',
  };
}
