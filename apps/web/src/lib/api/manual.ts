import { type ApiResult, apiGet } from './client';

/**
 * Typed bindings for the manual reference dataset.
 *
 * Every path and every field below is read from the gateway router
 * `services/api_gateway/routers/manual_data.py` and from the published contract
 * in `openapi.json`. The router returns pandas records, so a row is an object
 * whose keys are the dataset's own column names. Nothing here renames a column,
 * adds a unit, or fills a missing value: a surface that cannot prove a field
 * renders the honest unavailable state instead.
 */

export const MANUAL_BASE = '/api/v1/manual';

export const MANUAL_STATUS_SOURCE = `${MANUAL_BASE}/status`;
export const MANUAL_SITES_SOURCE = `${MANUAL_BASE}/sites`;
export const MANUAL_CROP_PARAMS_SOURCE = `${MANUAL_BASE}/crop-params`;
export const MANUAL_SOIL_REGIONS_SOURCE = `${MANUAL_BASE}/soil-regions`;
export const MANUAL_CROP_CALENDAR_SOURCE = `${MANUAL_BASE}/crop-calendar`;

/** The exact path a page fetched, so provenance never names a substitute. */
export function manualSiteSource(siteId: string): string {
  return `${MANUAL_BASE}/sites/${encodeURIComponent(siteId)}`;
}

export function manualWeatherDailySource(siteId: string): string {
  return `${MANUAL_BASE}/weather-daily/${encodeURIComponent(siteId)}`;
}

export function manualClimateNormalsSource(siteId: string): string {
  return `${MANUAL_BASE}/climate-normals/${encodeURIComponent(siteId)}`;
}

/** A value the gateway can put in a dataset cell. */
export type ManualValue = string | number | boolean | null;

/** One dataset row. Keys are the dataset's column names, never a UI invention. */
export type ManualRecord = Record<string, ManualValue>;

/** `GET /api/v1/manual/status` — existence, size and table inventory. */
export interface ManualStatus {
  exists: boolean;
  path?: string;
  size_mb?: number;
  tables?: Record<string, number>;
}

/** `GET /api/v1/manual/sites` — the router selects a fixed column list. */
export interface ManualSite {
  site_id: ManualValue;
  country?: ManualValue;
  admin1_city?: ManualValue;
  province?: ManualValue;
  lat?: ManualValue;
  lon?: ManualValue;
  elevation_m?: ManualValue;
  koppen?: ManualValue;
  annual_rain_normal_mm?: ManualValue;
}

export interface ManualSitesResponse {
  count: number;
  sites: ManualSite[];
}

export interface ManualRowsResponse {
  count: number;
  rows: ManualRecord[];
}

export interface ManualRegionsResponse {
  count: number;
  regions: ManualRecord[];
}

export interface ManualCropsResponse {
  count: number;
  crops: ManualRecord[];
}

export interface ManualMonthsResponse {
  count: number;
  months: ManualRecord[];
}

function query(source: string, params: Record<string, string | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, value);
  }
  const serialized = search.toString();
  return serialized ? `${source}?${serialized}` : source;
}

/**
 * A site is a numeric key in the dataset (`loader.py::site` matches `site_id`
 * against an integer), so only a non-negative integer can address a record.
 * The three site-scoped routes share this guard instead of repeating the rule,
 * and a value it rejects is a real 404 rather than a request the gateway would
 * answer with a server error.
 */
export function manualSitesPathGuard(siteId: string): boolean {
  return /^\d+$/.test(siteId);
}

/**
 * Keeps only object rows and leaves every other value untouched.
 *
 * The router serialises dataframe records, so a row is expected to be a plain
 * object. A row that is not one is dropped rather than guessed at, and the
 * caller still shows the `count` the gateway reported, so a mismatch between
 * the declared count and the rendered rows stays visible instead of hidden.
 */
export function toRecords(value: unknown): ManualRecord[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (row): row is ManualRecord => typeof row === 'object' && row !== null && !Array.isArray(row),
  );
}

/**
 * Column names in first-seen order, taken from the response itself.
 *
 * The OpenAPI schema for these routes is `additionalProperties: true`, so the
 * contract does not enumerate columns and the frontend must not invent a table
 * shape. Reading the keys back from the payload is the only honest option.
 */
export function columnsOf(records: readonly ManualRecord[]): string[] {
  const columns: string[] = [];
  const seen = new Set<string>();
  for (const record of records) {
    for (const key of Object.keys(record)) {
      if (seen.has(key)) continue;
      seen.add(key);
      columns.push(key);
    }
  }
  return columns;
}

/** Cell text for a value the server sent, with no invented formatting. */
export function formatCell(value: ManualValue | undefined): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  return String(value);
}

export function getManualStatus(): Promise<ApiResult<ManualStatus>> {
  return apiGet<ManualStatus>(MANUAL_STATUS_SOURCE);
}

export function listManualSites(search?: string): Promise<ApiResult<ManualSitesResponse>> {
  return apiGet<ManualSitesResponse>(query(MANUAL_SITES_SOURCE, { q: search }));
}

export function getManualSite(siteId: string): Promise<ApiResult<ManualRecord>> {
  return apiGet<ManualRecord>(manualSiteSource(siteId));
}

export function getManualWeatherDaily(
  siteId: string,
  limit?: number,
): Promise<ApiResult<ManualRowsResponse>> {
  return apiGet<ManualRowsResponse>(
    query(manualWeatherDailySource(siteId), limit ? { limit: String(limit) } : {}),
  );
}

export function getManualClimateNormals(siteId: string): Promise<ApiResult<ManualMonthsResponse>> {
  return apiGet<ManualMonthsResponse>(manualClimateNormalsSource(siteId));
}

export function getManualCropParams(speciesId?: string): Promise<ApiResult<ManualCropsResponse>> {
  return apiGet<ManualCropsResponse>(
    query(MANUAL_CROP_PARAMS_SOURCE, speciesId ? { species_id: speciesId } : {}),
  );
}

export function getManualSoilRegions(province?: string): Promise<ApiResult<ManualRegionsResponse>> {
  return apiGet<ManualRegionsResponse>(
    query(MANUAL_SOIL_REGIONS_SOURCE, province ? { province } : {}),
  );
}

export function getManualCropCalendar(
  province?: string,
  crop?: string,
): Promise<ApiResult<ManualRowsResponse>> {
  return apiGet<ManualRowsResponse>(
    query(MANUAL_CROP_CALENDAR_SOURCE, province ? { province, crop_fa: crop } : {}),
  );
}
