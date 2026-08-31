import type { ScientificChainResult } from '../types/vll';

const API_BASE = '/api';

export interface ChainOptions {
  crop?: string;
  plantingDate?: string;
  years?: number;
  slopePct?: number;
  optimize?: boolean;
  catchmentKm2?: number;
}

/**
 * اجرای زنجیره علمی کامل (RUSLE ← SWAT+ ← Pywr ← RothC ← AquaCrop ← HEC-RAS ← NSGA-II)
 * روی بک‌اند واقعی. هرگز داده ساختگی برنمی‌گرداند — فقط وضعیت‌های صادقانه (credentials_required /
 * requires_executable / no_observed_data) از سرویس.
 */
export async function fetchScientificChain(
  lat: number,
  lon: number,
  options: ChainOptions = {},
  onProgress?: (p: { status: string; stage?: string; progress: number }) => void
): Promise<ScientificChainResult> {
  const body = {
    lat,
    lon,
    crop: options.crop ?? 'wheat',
    planting_date: options.plantingDate ?? '2024-11-15',
    years: options.years ?? 20,
    slope_pct: options.slopePct ?? 10,
    optimize: options.optimize ?? true,
    catchment_km2: options.catchmentKm2 ?? 10,
  };

  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 300_000);
  try {
    const res = await fetch(`${API_BASE}/motors/chain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(
        `زنجیره علمی خطای HTTP ${res.status}${text ? `: ${text.slice(0, 200)}` : ''}`
      );
    }
    return (await res.json()) as ScientificChainResult;
  } finally {
    window.clearTimeout(timer);
  }
}
