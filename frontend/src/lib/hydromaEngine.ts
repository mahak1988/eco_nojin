/** Shared client + types for the HyDroMa engine tool APIs
 * (/api/v1/hydroma/indices and /api/v1/hydroma/soil). Both are pure,
 * stateless computation endpoints, so no bearer token is required (the
 * gateway CSRF middleware exempts the /api/v1/hydroma prefix). */

import { getApiBase } from './api';

export type EngineParamKind = 'float' | 'int' | 'str' | 'select' | 'list_float' | 'list_str';

export interface EngineParamSpec {
  name: string;
  label: string;
  unit?: string;
  kind: EngineParamKind;
  default?: number | string | number[] | string[];
  options?: string[];
  optional?: boolean;
}

export interface EngineModelMeta {
  id: string;
  name_en: string;
  description: string;
  reference: string;
  params: EngineParamSpec[];
}

export interface EngineRunResponse {
  id: string;
  result: Record<string, unknown>;
}

export interface EngineApiClient {
  list(): Promise<{ count: number; models: EngineModelMeta[] }>;
  detail(id: string): Promise<EngineModelMeta>;
  run(id: string, params: Record<string, unknown>): Promise<EngineRunResponse>;
}

async function request<T>(basePath: string, path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getApiBase()}${basePath}${path}`, init);
  } catch (error) {
    throw new Error(
      `hydroma_engine_network_error: ${error instanceof Error ? error.message : 'network error'}`,
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
    throw new Error(`hydroma_engine_error_${response.status}: ${JSON.stringify(detail)}`);
  }
  return (await response.json()) as T;
}

/** Builds an EngineApiClient bound to one engine tool namespace. */
export function makeEngineClient(basePath: string): EngineApiClient {
  return {
    list(): Promise<{ count: number; models: EngineModelMeta[] }> {
      return request(basePath, '');
    },
    detail(id: string): Promise<EngineModelMeta> {
      return request(basePath, `/${encodeURIComponent(id)}`);
    },
    run(id: string, params: Record<string, unknown>): Promise<EngineRunResponse> {
      return request(basePath, `/${encodeURIComponent(id)}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
    },
  };
}
