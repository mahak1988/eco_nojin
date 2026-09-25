import { backendRequest, readJson } from '@/lib/bff/backend';

export type WorkspaceResult<T> =
  | { ok: true; data: T; status: number }
  | { ok: false; error: string; status: number };

/**
 * Server-side read against the real gateway or BFF route.
 *
 * The session access token is attached here, on the server, so no
 * browser-supplied role or identity header ever reaches an upstream service. The
 * request is never cached: a professional surface must not serve a stale record.
 */
export async function workspaceGet<T>(
  accessToken: string,
  path: string,
): Promise<WorkspaceResult<T>> {
  try {
    const response = await backendRequest(path, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      accessToken,
    });
    const payload = await readJson(response);
    if (!response.ok) {
      return {
        ok: false,
        error: errorDetail(payload, response.statusText),
        status: response.status,
      };
    }
    return { ok: true, data: payload as T, status: response.status };
  } catch (error) {
    return { ok: false, error: errorMessage(error), status: 0 };
  }
}

/** Resolves several registered endpoints in parallel, keeping each result apart. */
export async function workspaceGetAll<T>(
  accessToken: string,
  paths: readonly string[],
): Promise<readonly WorkspaceResult<T>[]> {
  return Promise.all(paths.map((path) => workspaceGet<T>(accessToken, path)));
}

function errorDetail(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object' && 'detail' in payload) {
    return String((payload as { detail: unknown }).detail) || fallback;
  }
  return fallback;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
