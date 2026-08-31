import React, { useCallback, useEffect, useState } from 'react';
import { MapPin, RefreshCw, CloudRain, Thermometer, Droplets, Layers } from 'lucide-react';
import { fetchRealLand } from '../../services/realLandApi';
import type { RealLandResult } from '../../types/vll';

interface RealLandSummaryCardProps {
  onLoaded: (result: RealLandResult) => void;
  onCoordsChange?: (lat: number, lon: number) => void;
}

const DEFAULT_LAT = 35.5;
const DEFAULT_LON = 51.5;

/**
 * کارت «داده واقعی زمین» — اقلیم (Open-Meteo ERA5) + خاک (SoilGrids) + ماهواره (CDSE).
 * بدون fallback ساختگی: وضعیت ماهواره صادقانه (credentials_required) نمایش داده می‌شود.
 */
export const RealLandSummaryCard: React.FC<RealLandSummaryCardProps> = ({
  onLoaded,
  onCoordsChange,
}) => {
  const [lat, setLat] = useState(DEFAULT_LAT);
  const [lon, setLon] = useState(DEFAULT_LON);
  const [result, setResult] = useState<RealLandResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (latitude: number, longitude: number) => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchRealLand(latitude, longitude);
        setResult(data);
        onLoaded(data);
        onCoordsChange?.(latitude, longitude);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'خطا در دریافت داده واقعی زمین');
      } finally {
        setLoading(false);
      }
    },
    [onLoaded]
  );

  useEffect(() => {
    void load(DEFAULT_LAT, DEFAULT_LON);
  }, [load]);

  const soil = result?.soil;
  const climate = result?.climate;
  const satStatus = result?.satellite?.status;

  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
        }}
      >
        <h3
          style={{
            fontSize: '1.1rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <MapPin size={18} color="var(--color-primary)" /> داده واقعی زمین
        </h3>
        <span className="badge badge-success">۱۰۰٪ واقعی</span>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="number"
          step="0.01"
          value={lat}
          onChange={(e) => setLat(Number(e.target.value))}
          placeholder="عرض جغرافیایی"
          aria-label="عرض جغرافیایی"
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            borderRadius: 10,
            border: '1px solid var(--color-border)',
            background: 'var(--color-bg)',
            color: 'var(--color-text)',
            fontSize: '0.9rem',
          }}
        />
        <input
          type="number"
          step="0.01"
          value={lon}
          onChange={(e) => setLon(Number(e.target.value))}
          placeholder="طول جغرافیایی"
          aria-label="طول جغرافیایی"
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            borderRadius: 10,
            border: '1px solid var(--color-border)',
            background: 'var(--color-bg)',
            color: 'var(--color-text)',
            fontSize: '0.9rem',
          }}
        />
        <button
          onClick={() => void load(lat, lon)}
          disabled={loading}
          className="btn btn-primary"
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 10,
            border: 'none',
            cursor: 'pointer',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} /> بارگذاری
        </button>
      </div>

      {error && <p style={{ color: '#ef4444', fontSize: '0.9rem' }}>{error}</p>}

      {result && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '0.75rem',
          }}
        >
          <div className="stat-mini">
            <CloudRain size={16} color="#3b82f6" />
            <span>بارش سالانه</span>
            <strong>{climate?.annual_rainfall_mm?.toFixed(1) ?? '—'} mm</strong>
          </div>
          <div className="stat-mini">
            <Thermometer size={16} color="#f59e0b" />
            <span>دمای میانگین</span>
            <strong>{climate?.avg_temp_c?.toFixed(1) ?? '—'} °C</strong>
          </div>
          <div className="stat-mini">
            <Droplets size={16} color="#10b981" />
            <span>بافت خاک / SOC</span>
            <strong>
              {soil?.texture ?? '—'} ·{' '}
              {soil?.soc_g_kg ? `${(soil.soc_g_kg / 10).toFixed(2)}٪` : '—'}
            </strong>
          </div>
          <div className="stat-mini">
            <Layers size={16} color="#8b5cf6" />
            <span>ماهواره (CDSE)</span>
            <strong>
              {satStatus === 'ok'
                ? '✅ آماده'
                : satStatus === 'credentials_required'
                  ? '🔑 نیاز به اعتبار'
                  : '—'}
            </strong>
          </div>
        </div>
      )}

      {loading && (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
          در حال دریافت از Open-Meteo / SoilGrids / CDSE…
        </p>
      )}

      <style>{`
        .stat-mini { display: flex; flex-direction: column; gap: 0.25rem; padding: 0.75rem; border-radius: 12px; background: var(--color-bg); border: 1px solid var(--color-border); font-size: 0.8rem; color: var(--color-text-secondary); }
        .stat-mini strong { font-size: 1rem; color: var(--color-text); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};
