// Real backend client. Pages bind to the live API gateway; no mock data layer exists.

const API_BASE =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

export type ApiOk<T> = { ok: true; data: T; status: number };
export type ApiErr = { ok: false; error: string; status: number };
export type ApiResult<T> = ApiOk<T> | ApiErr;

export async function apiGet<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const url = `${API_BASE}${path}`;
  try {
    const res = await fetch(url, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
      ...init,
    });
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

export async function apiPost<T>(path: string, body?: unknown): Promise<ApiResult<T>> {
  const url = `${API_BASE}${path}`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      cache: 'no-store',
      headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
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
