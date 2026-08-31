/**
 * RealLandLoader — بارگذاری زمین واقعی (Phase 1)
 *
 * Lets the user pick a lat/lon and load REAL land intelligence:
 *   - Sentinel-2 NDVI / LAI / C-factor + Landsat LST + Sentinel-1 (CDSE)
 *   - ERA5 climate series (Open-Meteo, no key)
 *   - SoilGrids profile (texture, SOC, pH, CEC, BD, RUSLE K)
 *
 * Honesty: per-source status badges are shown exactly as reported by the
 * backend. No simulated fallback — if CDSE credentials are missing the
 * satellite badge shows "نیاز به ثبت‌نام رایگان" with a link.
 */
import React, { useState } from 'react';
import { MapPin, Loader2, Satellite, CloudRain, Layers } from 'lucide-react';
import { Card } from '../ui';
import { fetchRealLand } from '../../services/realLandApi';
import type { RealLandResult } from '../../types/vll';

interface RealLandLoaderProps {
  onLoaded: (result: RealLandResult) => void;
}

const DEFAULT_LAT = 35.5;
const DEFAULT_LON = 51.5;

const TEXTURE_FA: Record<string, string> = {
  sand: 'شنی',
  loam: 'لومی',
  clay: 'رسی',
  silt_loam: 'لوم سیلتی',
  sandy_loam: 'لوم شنی',
  clay_loam: 'لوم رسی',
};

function statusBadge(status: string | undefined): { label: string; color: string } {
  if (status === 'ok') return { label: '✅ فعال', color: '#22c55e' };
  if (status === 'credentials_required' || status === 'not_configured')
    return { label: '⚠️ نیاز به ثبت‌نام', color: '#f59e0b' };
  if (status === 'no_scene') return { label: '🌫 بدون صحنه', color: '#94a3b8' };
  if (status === 'error') return { label: '❌ خطا', color: '#ef4444' };
  return { label: '⏸ نامشخص', color: '#94a3b8' };
}

function Metric({ label, value, unit }: { label: string; value: React.ReactNode; unit?: string }) {
  return (
    <div
      style={{
        background: 'var(--color-surface-2, #f8fafc)',
        borderRadius: '0.5rem',
        padding: '0.4rem 0.6rem',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '0.8125rem',
      }}
    >
      <span style={{ opacity: 0.75 }}>{label}</span>
      <strong>
        {value ?? '—'}{' '}
        {unit ? <span style={{ fontSize: '0.7rem', opacity: 0.7 }}>{unit}</span> : null}
      </strong>
    </div>
  );
}

export const RealLandLoader: React.FC<RealLandLoaderProps> = ({ onLoaded }) => {
  const [lat, setLat] = useState<number>(DEFAULT_LAT);
  const [lon, setLon] = useState<number>(DEFAULT_LON);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RealLandResult | null>(null);

  const load = async () => {
    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      setError('مختصات معتبر وارد کنید (lat: -90..90, lon: -180..180)');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRealLand(lat, lon);
      setResult(data);
      onLoaded(data);
    } catch (e) {
      setError(
        e instanceof Error
          ? `خطا در دریافت داده واقعی: ${e.message} — مطمئن شوید سرور بک‌اند (پورت ۸۰۰۰) روشن است.`
          : 'خطای ناشناخته در دریافت داده واقعی'
      );
    } finally {
      setLoading(false);
    }
  };

  const sat = result?.satellite;
  const cli = result?.climate;
  const soil = result?.soil;
  const satBadge = statusBadge(sat?.status);
  const cliBadge = statusBadge(cli?.status);
  const soilBadge = statusBadge(soil?.status);

  return (
    <Card title="🌍 بارگذاری زمین واقعی" icon={<MapPin size={18} />} className="mb-4">
      {/* Coordinates */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.6rem' }}>
        <label style={{ flex: 1, fontSize: '0.75rem', opacity: 0.75 }}>
          عرض جغرافیایی (lat)
          <input
            type="number"
            step="0.0001"
            min={-90}
            max={90}
            value={lat}
            onChange={(e) => setLat(parseFloat(e.target.value))}
            style={{
              width: '100%',
              marginTop: '0.2rem',
              padding: '0.4rem 0.5rem',
              borderRadius: '0.4rem',
              border: '1px solid var(--color-border)',
              fontSize: '0.875rem',
            }}
          />
        </label>
        <label style={{ flex: 1, fontSize: '0.75rem', opacity: 0.75 }}>
          طول جغرافیایی (lon)
          <input
            type="number"
            step="0.0001"
            min={-180}
            max={180}
            value={lon}
            onChange={(e) => setLon(parseFloat(e.target.value))}
            style={{
              width: '100%',
              marginTop: '0.2rem',
              padding: '0.4rem 0.5rem',
              borderRadius: '0.4rem',
              border: '1px solid var(--color-border)',
              fontSize: '0.875rem',
            }}
          />
        </label>
      </div>

      <button
        onClick={load}
        disabled={loading}
        className="btn btn-primary"
        style={{ width: '100%', justifyContent: 'center' }}
      >
        {loading ? <Loader2 size={16} className="spin" /> : <Satellite size={16} />}
        {loading ? 'در حال دریافت داده واقعی...' : 'بارگذاری زمین واقعی'}
      </button>

      {error && (
        <div
          style={{
            marginTop: '0.6rem',
            padding: '0.5rem 0.6rem',
            background: '#fef2f2',
            color: '#b91c1c',
            borderRadius: '0.5rem',
            fontSize: '0.8rem',
          }}
        >
          {error}
        </div>
      )}

      {result && !error && (
        <div
          style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}
        >
          {/* Source badges */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
            <Badge
              icon={<Satellite size={12} />}
              label="ماهواره Copernicus (CDSE)"
              badge={satBadge}
            />
            <Badge
              icon={<CloudRain size={12} />}
              label="اقلیم ERA5 (Open-Meteo)"
              badge={cliBadge}
            />
            <Badge icon={<Layers size={12} />} label="خاک SoilGrids (ISRIC)" badge={soilBadge} />
          </div>

          {sat?.status === 'credentials_required' && (
            <div
              style={{
                padding: '0.5rem 0.6rem',
                background: '#fffbeb',
                color: '#92400e',
                borderRadius: '0.5rem',
                fontSize: '0.75rem',
                lineHeight: 1.6,
              }}
            >
              برای داده واقعی ماهواره، در{' '}
              <a
                href="https://dataspace.copernicus.eu"
                target="_blank"
                rel="noreferrer"
                style={{ color: '#b45309', fontWeight: 600 }}
              >
                dataspace.copernicus.eu
              </a>{' '}
              رایگان ثبت‌نام کنید و CDSE_CLIENT_ID / CDSE_CLIENT_SECRET را در فایل <code>.env</code>{' '}
              بک‌اند قرار دهید. اقلیم و خاک هم‌اکنون واقعی هستند.
            </div>
          )}

          {/* Satellite metrics */}
          {(sat?.status === 'ok' || sat?.status === 'no_scene') && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
              <Metric label="NDVI" value={sat?.ndvi?.toFixed(3)} />
              <Metric label="LAI" value={sat?.lai?.toFixed(2)} />
              <Metric label="ضریب C (RUSLE)" value={sat?.c_factor?.toFixed(3)} />
              <Metric label="دمای سطح (LST)" value={sat?.lst_c?.toFixed(1)} unit="°C" />
            </div>
          )}

          {/* Climate metrics */}
          {cli?.status === 'ok' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
              <Metric label="بارش سالانه" value={cli?.annual_rainfall_mm?.toFixed(0)} unit="mm" />
              <Metric label="دمای میانگین" value={cli?.avg_temp_c?.toFixed(1)} unit="°C" />
              <Metric label="ET₀ سالانه" value={cli?.annual_et0_mm?.toFixed(0)} unit="mm" />
              <Metric
                label="آخرین بارش"
                value={cli?.latest?.precipitation_mm?.toFixed(1)}
                unit="mm"
              />
            </div>
          )}

          {/* Soil metrics */}
          {soil?.status === 'ok' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.3rem' }}>
              <Metric label="بافت خاک" value={TEXTURE_FA[soil?.texture ?? ''] ?? soil?.texture} />
              <Metric label="کربن آلی" value={soil?.soc_pct?.toFixed(2)} unit="%" />
              <Metric label="pH" value={soil?.ph_h2o?.toFixed(1)} />
              <Metric label="K (RUSLE)" value={soil?.k_factor_rusle?.toFixed(3)} />
            </div>
          )}

          {soil?.status === 'ok' && soil.sample_offset_km != null && soil.sample_offset_km > 2 && (
            <div style={{ fontSize: '0.7rem', opacity: 0.7 }}>
              ⓘ خاک از پیکسل SoilGrids در فاصله {soil.sample_offset_km} کیلومتری نمونه‌برداری شد.
            </div>
          )}

          <div style={{ fontSize: '0.7rem', opacity: 0.6, textAlign: 'center' }}>
            همه منابع رایگان —{' '}
            {result.summary.all_real ? '✅ ۱۰۰٪ داده واقعی' : 'منابع واقعی: اقلیم + خاک'}
          </div>
        </div>
      )}
    </Card>
  );
};

function Badge({
  icon,
  label,
  badge,
}: {
  icon: React.ReactNode;
  label: string;
  badge: { label: string; color: string };
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        padding: '0.3rem 0.5rem',
        background: 'var(--color-surface-2, #f8fafc)',
        borderRadius: '0.4rem',
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
        {icon} {label}
      </span>
      <span
        style={{
          color: badge.color,
          fontWeight: 600,
          whiteSpace: 'nowrap',
        }}
      >
        {badge.label}
      </span>
    </div>
  );
}
