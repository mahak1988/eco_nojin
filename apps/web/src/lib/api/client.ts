// Real backend client. Pages bind to the live API gateway; no mock data layer exists.

import { publicEnv, resolveApiUrl } from '@/lib/config/public-env';

let apiBase = publicEnv.apiBaseUrl;

export function setApiBaseUrl(baseUrl: string): void {
  const normalized = baseUrl.replace(/\/+$/, '');
  if (process.env.NODE_ENV === 'production' && !normalized.startsWith('/')) {
    throw new Error('Production API base URL must be same-origin');
  }
  apiBase = normalized;
}

function requestUrl(path: string): string {
  if (typeof window === 'undefined' && apiBase === publicEnv.apiBaseUrl) {
    return resolveApiUrl(path);
  }
  return `${apiBase}${path}`;
}

function createRequestId(): string {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function createIdempotencyKey(): string {
  if (typeof globalThis.crypto?.randomUUID === 'function') {
    return globalThis.crypto.randomUUID();
  }
  if (typeof globalThis.crypto?.getRandomValues === 'function') {
    const bytes = new Uint8Array(32);
    globalThis.crypto.getRandomValues(bytes);
    return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
  }
  throw new Error('A secure random source is required for idempotency keys');
}

function withRequestHeaders(init: RequestInit = {}): RequestInit {
  const headers = new Headers(init.headers);
  const method = (init.method ?? 'GET').toUpperCase();
  if (!headers.has('X-Request-ID')) {
    headers.set('X-Request-ID', createRequestId());
  }
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRF-Intent', '1');
  }
  return { ...init, headers, credentials: 'same-origin' };
}

export type ApiOk<T> = { ok: true; data: T; status: number };
export type ApiErr = { ok: false; error: string; status: number };
export type ApiResult<T> = ApiOk<T> | ApiErr;

export async function apiGet<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const url = requestUrl(path);
  try {
    const res = await fetch(
      url,
      withRequestHeaders({
        cache: 'no-store',
        headers: { Accept: 'application/json' },
        ...init,
      }),
    );
    const text = await res.text();
    let parsed: unknown;
    try {
      parsed = text ? JSON.parse(text) : undefined;
    } catch {
      parsed = text;
    }
    if (!res.ok) {
      const detail =
        typeof parsed === 'string'
          ? parsed.slice(0, 300)
          : (((parsed as Record<string, unknown> | undefined)?.detail as string) ?? res.statusText);
      return { ok: false, error: String(detail ?? 'request failed'), status: res.status };
    }
    return { ok: true, data: parsed as T, status: res.status };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err), status: 0 };
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  const url = requestUrl(path);
  try {
    const headers = new Headers(init.headers);
    headers.set('Accept', 'application/json');
    const res = await fetch(url, withRequestHeaders({ cache: 'no-store', ...init, headers }));
    const text = await res.text();
    let parsed: unknown;
    try {
      parsed = text ? JSON.parse(text) : undefined;
    } catch {
      parsed = text;
    }
    if (!res.ok) {
      const detail =
        typeof parsed === 'string'
          ? parsed.slice(0, 300)
          : (((parsed as Record<string, unknown> | undefined)?.detail as string) ?? res.statusText);
      return { ok: false, error: String(detail ?? 'request failed'), status: res.status };
    }
    return { ok: true, data: parsed as T, status: res.status };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err), status: 0 };
  }
}

export async function apiPatch<T>(
  path: string,
  body?: unknown,
  init: RequestInit = {},
): Promise<ApiResult<T>> {
  return apiRequest<T>(path, {
    ...init,
    method: 'PATCH',
    body: body === undefined ? undefined : JSON.stringify(body),
    headers: {
      ...Object.fromEntries(new Headers(init.headers)),
      'Content-Type': 'application/json',
    },
  });
}

export async function apiDelete<T>(path: string, init: RequestInit = {}): Promise<ApiResult<T>> {
  return apiRequest<T>(path, { ...init, method: 'DELETE' });
}

export type PlatformStats = {
  cpp_available: boolean;
  db_backend: string;
  db_reachable: boolean;
  total_landscapes: number | null;
  total_projects: number | null;
  active_projects: number | null;
  error?: string;
};

export type PlatformHealth = {
  status: string;
  service: string;
  cpp_available: boolean;
  db_backend: string;
  db_reachable: boolean;
};

export type LandProfile = {
  id: string;
  name: string;
  location_lat: number | null;
  location_lon: number | null;
  area_ha: number | null;
  created_at: string | null;
};

export type MarketProduct = {
  id: string;
  name: string;
  slug?: string;
  category: string;
  description: string;
  price_per_kg: number;
  quantity_available_kg: number;
  organic_certified: boolean;
  producer_name: string;
  origin_location?: string;
};

export type MarketProducts = { products: MarketProduct[] };

export type MarketStats = {
  total_products: number;
  total_producers: number;
  organic_products: number;
};

export async function apiPost<T>(
  path: string,
  body?: unknown,
  init: RequestInit = {},
): Promise<ApiResult<T>> {
  const url = requestUrl(path);
  try {
    const headers = new Headers(init.headers);
    headers.set('Accept', 'application/json');
    if (body !== undefined) headers.set('Content-Type', 'application/json');
    const res = await fetch(
      url,
      withRequestHeaders({
        method: 'POST',
        cache: 'no-store',
        ...init,
        headers,
        body: body !== undefined ? JSON.stringify(body) : init.body,
      }),
    );
    const text = await res.text();
    let parsed: unknown;
    try {
      parsed = text ? JSON.parse(text) : undefined;
    } catch {
      parsed = text;
    }
    if (!res.ok) {
      const detail =
        typeof parsed === 'string'
          ? parsed.slice(0, 300)
          : (((parsed as Record<string, unknown> | undefined)?.detail as string) ?? res.statusText);
      return { ok: false, error: String(detail ?? 'request failed'), status: res.status };
    }
    return { ok: true, data: parsed as T, status: res.status };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err), status: 0 };
  }
}

export type HydromaModel = {
  id: string;
  name: string;
  category: string;
  description: string;
  version: string;
  language: string;
  reference?: string;
};

export type CppStatus = {
  available: boolean;
  dll: string | null;
  kernels: string[];
  note?: string;
};
