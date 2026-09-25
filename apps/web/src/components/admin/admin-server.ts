import { cookies } from 'next/headers';
import { backendRequest, readJson } from '@/lib/bff/backend';
import { type SessionRecord, sessionCookieName } from '@/lib/session/session-cookie';
import { getStoredSession } from '@/lib/session/store';

export type AdminResult<T> =
  | { ok: true; data: T; status: number }
  | { ok: false; error: string; status: number };

/**
 * Deny by default, exactly like the console layout: a missing cookie, an
 * expired record or an unreachable store all resolve to "no session".
 */
export async function readAdminSession(): Promise<SessionRecord | null> {
  try {
    const store = await cookies();
    const id = store.get(sessionCookieName())?.value;
    return id ? await getStoredSession(id) : null;
  } catch {
    return null;
  }
}

/**
 * The access token for gateway calls. Public endpoints tolerate an empty token;
 * the BFF only attaches the header when a value exists.
 */
export function adminToken(session: SessionRecord | null): string {
  return session?.accessToken ?? '';
}

/**
 * Server-side read against the real gateway using the session access token.
 * The request is never cached: an admin console must not serve a stale matrix.
 */
export async function adminGet<T>(accessToken: string, path: string): Promise<AdminResult<T>> {
  try {
    const response = await backendRequest(path, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      accessToken,
    });
    const payload = await readJson(response);
    if (!response.ok) {
      const detail =
        payload && typeof payload === 'object' && 'detail' in payload
          ? String((payload as { detail: unknown }).detail)
          : response.statusText;
      return { ok: false, error: detail || 'request failed', status: response.status };
    }
    return { ok: true, data: payload as T, status: response.status };
  } catch (error) {
    return { ok: false, error: error instanceof Error ? error.message : String(error), status: 0 };
  }
}
