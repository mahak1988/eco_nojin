/** Typed HTTP client for the live HyDroMa gateway (Phase A/B).
 *  - Centralizes base URL, bearer token and error mapping.
 *  - POST calls send the JWT because the gateway CSRF middleware exempts
 *    Bearer clients; anonymous POSTs are rejected with 403.
 *  - Role-protected endpoints (motors/site-run/*) return 403 for non-admins;
 *    describeError() turns both cases into actionable UI hints. */

import { getApiBase } from './api';

const TOKEN_KEY = 'hydrom…oken';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable */
  }
}

export function isLoggedIn(): boolean {
  return Boolean(getToken());
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(`api_error_${status}`);
    this.status = status;
    this.detail = detail;
  }
}

/** Human/actionable classification of an error (used by the live UI). */
export type ErrorKind =
  'network' | 'csrf' | 'role' | 'validation' | 'notfound' | 'server' | 'unknown';

export function classifyError(error: unknown): ErrorKind {
  if (!(error instanceof ApiError)) return 'unknown';
  const text = JSON.stringify(error.detail ?? '');
  if (error.status === 0) return 'network';
  if (error.status === 403 && text.toLowerCase().includes('csrf')) return 'csrf';
  if (error.status === 403) return 'role';
  if (error.status === 422 || error.status === 400) return 'validation';
  if (error.status === 404) return 'notfound';
  if (error.status >= 500) return 'server';
  return 'unknown';
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  auth?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', query, body, auth = true } = options;
  // Relative URLs must stay relative: the Vite dev proxy and the
  // same-origin production deploy both serve /api from the current origin.
  // `new URL('/api/...')` throws for relative paths, so build the query
  // string with URLSearchParams and fetch the plain URL instead.
  let url = `${getApiBase()}${path}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== '') params.set(key, String(value));
    }
    const qs = params.toString();
    if (qs) url += (url.includes('?') ? '&' : '?') + qs;
  }
  const headers: Record<string, string> = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    throw new ApiError(0, error instanceof Error ? error.message : 'network error');
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      const parsed = (await response.json()) as { detail?: unknown };
      detail = parsed.detail ?? parsed;
    } catch {
      detail = null;
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

/* ---- auth (A1) ---- */

export interface LoginBody {
  email: string;
  password: string;
}

export interface UserResponse {
  id?: string;
  email?: string;
  full_name?: string;
  role?: string;
  language?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  user?: UserResponse;
}

/** Roles accepted by the gateway registration endpoint. */
export const REGISTERABLE_ROLES = [
  'farmer',
  'researcher',
  'organization',
  'tourist',
  'regular',
] as const;

export const authApi = {
  login(body: LoginBody): Promise<TokenResponse> {
    return request('/api/v1/auth/login', { method: 'POST', body });
  },
  register(body: Record<string, unknown>): Promise<TokenResponse> {
    return request('/api/v1/auth/register', { method: 'POST', body });
  },
  me(): Promise<UserResponse> {
    return request('/api/v1/auth/me');
  },
};

/* ---- health (A8) ---- */

export interface HealthEntry {
  key: string;
  path: string;
  ok: boolean;
  status: number;
  latencyMs: number;
  note?: string;
}

export async function fetchAllHealth(): Promise<HealthEntry[]> {
  const probes = [
    { key: 'root', path: '/health' },
    { key: 'motors', path: '/api/v1/motors/health' },
    { key: 'satellite', path: '/api/v1/satellite/health' },
    { key: 'land', path: '/api/v1/land/health' },
    { key: 'stores', path: '/api/v1/satellite/stores/status' },
    { key: 'cds', path: '/api/v1/satellite/cds/status' },
    { key: 'pinn', path: '/api/v1/models/pinn-status' },
    { key: 'cpp', path: '/api/v1/models/cpp-status' },
    { key: 'zenodo', path: '/api/v1/science/zenodo/status' },
    { key: 'rate-limit', path: '/api/v1/auth/rate-limit' },
  ];
  return Promise.all(
    probes.map(async (probe) => {
      const started = performance.now();
      try {
        const response = await fetch(`${getApiBase()}${probe.path}`, {
          headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : undefined,
        });
        return {
          key: probe.key,
          path: probe.path,
          ok: response.ok,
          status: response.status,
          latencyMs: Math.round(performance.now() - started),
        };
      } catch {
        return {
          key: probe.key,
          path: probe.path,
          ok: false,
          status: 0,
          latencyMs: 0,
          note: 'unreachable',
        };
      }
    }),
  );
}

/* ---- satellite (A2) ---- */

export const satelliteApi = {
  weather(lat: number, lon: number, days = 7): Promise<Record<string, unknown>> {
    return request('/api/v1/satellite/weather', { query: { lat, lon, days } });
  },
  era5Series(params: {
    lat: number;
    lon: number;
    start: string;
    end: string;
    variables?: string;
  }): Promise<Record<string, unknown>> {
    return request('/api/v1/satellite/era5/series', { query: params });
  },
  /** NDVI scene analysis — permissioned (requires CDSE credentials / auth). */
  analyze(lat: number, lon: number): Promise<Record<string, unknown>> {
    return request('/api/v1/satellite/analyze', { method: 'POST', body: { lat, lon } });
  },
  indices(): Promise<unknown> {
    return request('/api/v1/satellite/indices');
  },
  providers(): Promise<unknown> {
    return request('/api/v1/satellite/providers');
  },
};

/* ---- scientific models / indices (A5) ---- */

export const modelsApi = {
  list(): Promise<Record<string, unknown>> {
    return request('/api/v1/models');
  },
  detail(slug: string): Promise<Record<string, unknown>> {
    return request(`/api/v1/models/${encodeURIComponent(slug)}`);
  },
  run(slug: string, params: Record<string, unknown> = {}): Promise<Record<string, unknown>> {
    return request(`/api/v1/models/${encodeURIComponent(slug)}/run`, {
      method: 'POST',
      body: params,
    });
  },
};

/* ---- scientific chain (A4) ---- */

export interface ChainRequest {
  lat: number;
  lon: number;
  crop?: string;
  planting_date?: string;
  years?: number;
  slope_pct?: number;
  practice?: string;
  irrigation_threshold_mm?: number;
  optimize?: boolean;
  catchment_km2?: number;
}

export const chainApi = {
  motors(body: ChainRequest): Promise<Record<string, unknown>> {
    return request('/api/v1/motors/chain', { method: 'POST', body });
  },
  simulation(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request('/api/v1/simulation/run', { method: 'POST', body });
  },
  motorsList(): Promise<unknown> {
    return request('/api/v1/motors/list');
  },
};

/* ---- scientific motors incl. economy (A3/B-economy) ---- */

export interface ManualSiteRun {
  site_id: string;
  crop_name?: string;
  planting_date?: string;
  sim_start?: string;
  sim_end?: string;
  season_days?: number;
  irrigation_threshold_mm?: number;
  soil_province?: string;
}

export const motorsApi = {
  /** Admin-only motors (economy, aquacrop, rothc, what_if, swat_plus, hecras). */
  siteRun(motor: string, body: ManualSiteRun): Promise<Record<string, unknown>> {
    return request(`/api/v1/motors/site-run/${motor}`, { method: 'POST', body });
  },
  manualSites(): Promise<unknown> {
    return request('/api/v1/motors/manual-sites');
  },
  run(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request('/api/v1/motors/run', { method: 'POST', body });
  },
};

/* ---- soil (A6) ---- */

export const soilApi = {
  analyze(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request('/api/v1/soil/analyze', { method: 'POST', body });
  },
  erosion(params: {
    slope_length_m: number;
    slope_percent: number;
    annual_rainfall_mm: number;
    texture: string;
    c_factor: number;
    p_factor: number;
  }): Promise<Record<string, unknown>> {
    return request('/api/v1/soil/erosion', { query: params });
  },
};

/* ---- carbon (A7) ---- */

export const carbonApi = {
  budget(body: Record<string, unknown>): Promise<Record<string, unknown>> {
    return request('/api/v1/mrv/carbon-budget', { method: 'POST', body });
  },
  soilCarbon(params: Record<string, number>): Promise<Record<string, unknown>> {
    return request('/api/v1/carbon/soil-carbon', { method: 'POST', query: params });
  },
  standards(): Promise<unknown> {
    return request('/api/v1/carbon/standards');
  },
  species(): Promise<unknown> {
    return request('/api/v1/carbon/species');
  },
  projects(): Promise<unknown> {
    return request('/api/v1/carbon/projects');
  },
};

/* ---- land profiles (A6 companion) ---- */

export const landApi = {
  profiles(): Promise<unknown> {
    return request('/api/v1/land/profiles');
  },
};
