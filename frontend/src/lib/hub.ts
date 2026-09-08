/** HyDroMa data-hub client — per-user (anonymous client key) aggregation of
 * model runs. The key lives in localStorage; when platform auth lands, the
 * key is bound to the account server-side. No PII, no IP (data minimization). */

const CLIENT_KEY_STORAGE = 'hydroma-client-id';
import { getApiBase } from './api';

export function getClientId(): string {
  try {
    const existing = localStorage.getItem(CLIENT_KEY_STORAGE);
    if (existing && /^[A-Za-z0-9_-]{8,64}$/.test(existing)) return existing;
    const generated =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID().replace(/-/g, '').slice(0, 32)
        : `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
    localStorage.setItem(CLIENT_KEY_STORAGE, generated);
    return generated;
  } catch (error) {
    console.warn('client id generation failed', error);
    return 'anonymous-fallback-key';
  }
}

export interface HubRun {
  id: string;
  model_id: string;
  title: string | null;
  inputs: Record<string, unknown> | null;
  outputs: Record<string, unknown> | null;
  shared: boolean;
  created_at: string | null;
}

export interface HubRunPayload {
  modelId: string;
  title?: string;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
}

/** Registers a model run in the central aggregation hub. */
export async function submitHubRun(
  payload: HubRunPayload,
  fetchImpl: typeof fetch = fetch,
): Promise<{ ok: boolean; id: string }> {
  const response = await fetchImpl(`${getApiBase()}/api/v1/hub/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_key: getClientId(), ...payload }),
  });
  if (!response.ok) throw new Error(`hub_submit_failed_${response.status}`);
  return (await response.json()) as { ok: boolean; id: string };
}

/** Lists this client's runs from the hub. */
export async function fetchHubRuns(fetchImpl: typeof fetch = fetch): Promise<HubRun[]> {
  const response = await fetchImpl(
    `${getApiBase()}/api/v1/hub/runs?user_key=${encodeURIComponent(getClientId())}`,
  );
  if (!response.ok) throw new Error(`hub_list_failed_${response.status}`);
  const body = (await response.json()) as { runs: HubRun[] };
  return body.runs;
}

/** Toggles the shared flag of one of this client's runs. */
export async function setHubRunShared(
  runId: string,
  shared: boolean,
  fetchImpl: typeof fetch = fetch,
): Promise<void> {
  const response = await fetchImpl(
    `${getApiBase()}/api/v1/hub/runs/${encodeURIComponent(runId)}/share?user_key=${encodeURIComponent(getClientId())}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ shared }),
    },
  );
  if (!response.ok) throw new Error(`hub_share_failed_${response.status}`);
}

/** Lists publicly shared runs (outputs shared by all users). */
export async function fetchSharedRuns(fetchImpl: typeof fetch = fetch): Promise<HubRun[]> {
  const response = await fetchImpl(`${getApiBase()}/api/v1/hub/shared`);
  if (!response.ok) throw new Error(`hub_shared_failed_${response.status}`);
  const body = (await response.json()) as { runs: HubRun[] };
  return body.runs;
}
