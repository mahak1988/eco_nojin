/**
 * Real Land API — بارگذاری زمین واقعی (Phase 1)
 *
 * Calls POST /api/v1/satellite/real-land which aggregates REAL free data:
 *   - satellite: Copernicus CDSE (Sentinel-2 NDVI/LAI/C-factor, Landsat LST,
 *     Sentinel-1 VV/VH proxy) — needs free CDSE credentials in backend .env
 *   - climate:   Open-Meteo ERA5 archive (rainfall, temperature, FAO-56 ET0)
 *   - soil:      ISRIC SoilGrids 2.0 (texture, SOC, pH, CEC, BD, RUSLE K)
 *
 * Honesty contract: this service NEVER fabricates data. The backend
 * reports per-source statuses (ok / error / credentials_required / ...)
 * and the UI shows them to the user as-is.
 */
import { API_BASE_URL } from '../config';
import type { RealLandResult } from '../types/vll';

const REQUEST_TIMEOUT_MS = 60_000;

export async function fetchRealLand(
  lat: number,
  lon: number,
  analysisDate?: string,
): Promise<RealLandResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/satellite/real-land`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon, analysis_date: analysisDate ?? null }),
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`real-land request failed with status ${response.status}`);
    }
    return (await response.json()) as RealLandResult;
  } finally {
    clearTimeout(timer);
  }
}
