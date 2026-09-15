/** Typed client for the HyDroMa scientific indices API
 * (/api/v1/hydroma/indices). These endpoints are pure, stateless
 * computations, so no bearer token is required (the gateway CSRF middleware
 * exempts this prefix). */

import { getApiBase } from './api';

export type IndexParamKind = 'float' | 'int' | 'str' | 'select' | 'list_float' | 'list_str';

export interface IndexParamSpec {
  name: string;
  label: string;
  unit?: string;
  kind: IndexParamKind;
  default?: number | string | number[] | string[];
  options?: string[];
}

export interface IndexModelMeta {
  id: string;
  name_en: string;
  description: string;
  reference: string;
  params: IndexParamSpec[];
}

export interface IndexRunResponse {
  id: string;
  result: Record<string, unknown>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getApiBase()}${path}`, init);
  } catch (error) {
    throw new Error(
      `hydroma_indices_network_error: ${error instanceof Error ? error.message : 'network error'}`,
      { cause: error },
    );
  }
  if (!response.ok) {
    let detail: unknown;
    try {
      const parsed = (await response.json()) as { detail?: unknown };
      detail = parsed.detail ?? parsed;
    } catch {
      detail = null;
    }
    throw new Error(`hydroma_indices_error_${response.status}: ${JSON.stringify(detail)}`);
  }
  return (await response.json()) as T;
}

export const hydromaIndicesApi = {
  list(): Promise<{ count: number; models: IndexModelMeta[] }> {
    return request('/api/v1/hydroma/indices');
  },
  detail(id: string): Promise<IndexModelMeta> {
    return request(`/api/v1/hydroma/indices/${encodeURIComponent(id)}`);
  },
  run(id: string, params: Record<string, unknown>): Promise<IndexRunResponse> {
    return request(`/api/v1/hydroma/indices/${encodeURIComponent(id)}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
  },
};

/** True when a model id is one of the eight live HyDroMa index models. */
export const HYGROMA_INDEX_IDS = [
  'ecsi',
  'epia',
  'esri',
  'ewsi',
  'hdvi',
  'hlhs',
  'hpheno',
  'hyrue',
] as const;

export function isHydromaIndexId(id: string): boolean {
  return (HYGROMA_INDEX_IDS as readonly string[]).includes(id);
}
