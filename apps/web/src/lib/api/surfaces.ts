import { type ApiResult, apiGet } from './client';

/**
 * Bindings for catalogue surfaces whose published response schema declares no
 * field. Every path below appears verbatim in `openapi.json`.
 *
 * The gateway routes behind these surfaces now declare their response envelope
 * (`PublicDashboardResponse`, `PublicRouterCheckResponse`,
 * `ManualStatusResponse`, `ManualSitesResponse`, `ManualRowsResponse`,
 * `ContentSearchResponse`), so the envelope is typed rather than `unknown`. The
 * `data` member stays dynamic on purpose: those routes aggregate heterogeneous
 * tables and the contract describes the envelope, not every cell — the frontend
 * reads the column set back from the payload instead of asserting one.
 */
export const DASHBOARD_PUBLIC_BASE = '/dashboard/public';

export const DASHBOARD_PUBLIC_SOURCES = {
  full: `${DASHBOARD_PUBLIC_BASE}/full`,
  projects: `${DASHBOARD_PUBLIC_BASE}/projects`,
  carbon: `${DASHBOARD_PUBLIC_BASE}/carbon`,
  analytics: `${DASHBOARD_PUBLIC_BASE}/analytics`,
  weather: `${DASHBOARD_PUBLIC_BASE}/weather`,
  satellite: `${DASHBOARD_PUBLIC_BASE}/satellite`,
  soil: `${DASHBOARD_PUBLIC_BASE}/soil`,
  mrv: `${DASHBOARD_PUBLIC_BASE}/mrv`,
  simulations: `${DASHBOARD_PUBLIC_BASE}/simulations`,
  tourism: `${DASHBOARD_PUBLIC_BASE}/tourism`,
  test: `${DASHBOARD_PUBLIC_BASE}/test`,
} as const;

export type DashboardPublicKey = keyof typeof DASHBOARD_PUBLIC_SOURCES;

export const MARKETPLACE_STATS_SOURCE = '/api/v1/marketplace/stats';
export const MARKETPLACE_PRODUCERS_SOURCE = '/api/v1/marketplace/producers';
export const CONTENT_SEARCH_SOURCE = '/api/v1/content/search';

function query(source: string, params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === '') continue;
    search.set(key, String(value));
  }
  const serialized = search.toString();
  return serialized ? `${source}?${serialized}` : source;
}

export function dashboardPublicSource(key: DashboardPublicKey, farmId?: string): string {
  return query(DASHBOARD_PUBLIC_SOURCES[key], { farm_id: farmId });
}

export function contentSearchSource(queryText: string, limit?: number): string {
  return query(CONTENT_SEARCH_SOURCE, { q: queryText, limit });
}

/**
 * The envelope every `/dashboard/public/*` route returns, as declared by
 * `PublicDashboardResponse` in `services/api_gateway/routers/dashboard.py`.
 * `data` stays dynamic because each route aggregates a different set of tables
 * and the contract describes the envelope rather than every cell.
 */
export interface PublicDashboardEnvelope {
  status: string;
  auth_required: boolean;
  data: Record<string, unknown>;
  timestamp: string;
}

/** `PublicRouterCheckResponse` — the reachability route, not a data surface. */
export interface PublicRouterCheckEnvelope {
  status: string;
  message: string;
  auth_required: boolean;
  version: string;
  schema_verified: boolean;
  available_endpoints: string[];
}

export function getDashboardPublic(
  key: DashboardPublicKey,
  farmId?: string,
): Promise<ApiResult<PublicDashboardEnvelope>> {
  return apiGet<PublicDashboardEnvelope>(dashboardPublicSource(key, farmId));
}

export function getMarketplaceStats(): Promise<ApiResult<unknown>> {
  return apiGet<unknown>(MARKETPLACE_STATS_SOURCE);
}

export function getMarketplaceProducers(): Promise<ApiResult<unknown>> {
  return apiGet<unknown>(MARKETPLACE_PRODUCERS_SOURCE);
}

export function searchContent(
  queryText: string,
  limit?: number,
): Promise<ApiResult<ContentSearchEnvelope>> {
  return apiGet<ContentSearchEnvelope>(contentSearchSource(queryText, limit));
}

/**
 * `ContentSearchResponse` from `services/api_gateway/routers/content_public.py`.
 * Declared there, so the frontend no longer has to treat a search result as an
 * arbitrary object.
 */
export interface ContentSearchHit {
  id: string;
  title: string;
  category: string;
  language: string;
  published_at: string | null;
  snippet: string;
}

export interface ContentSearchEnvelope {
  query: string;
  count: number;
  results: ContentSearchHit[];
}

/**
 * Whether the payload itself claims verification.
 *
 * A 200 only proves the gateway answered, not that the answer was measured. The
 * public dashboard router used to return hard-coded counters next to live ones —
 * it no longer does, but a stamp keyed on the HTTP status would still certify a
 * stored constant on any other route. Verification is therefore read from the
 * payload, and a route that asserts nothing is shown unverified.
 */
export function verificationOf(payload: unknown): boolean {
  if (typeof payload !== 'object' || payload === null || Array.isArray(payload)) return false;
  const record = payload as Record<string, unknown>;

  if (record.verified === true || record.schema_verified === true) return true;
  if (record.is_verified === true || record.data_verified === true) return true;

  const provenance = record.provenance;
  if (typeof provenance === 'object' && provenance !== null && !Array.isArray(provenance)) {
    return (provenance as Record<string, unknown>).verified === true;
  }
  return false;
}
