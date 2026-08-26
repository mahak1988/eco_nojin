import React, { useState } from 'react';
import { GitCompareArrows, Play, ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { fetchScientificChain } from '../../services/scientificChainApi';
import type { ScientificChainResult } from '../../types/vll';

interface ScenarioCompareProps {
  lat: number;
  lon: number;
  crop?: string;
}

interface Scenario {
  key: string;
  label: string;
  hint: string;
  slopePct: number;
}

const SCENARIOS: Scenario[] = [
  { key: 'baseline', label: 'سناریو الف (پایه)', hint: 'شیب ۱۰٪ — کشت فعلی', slopePct: 10 },
  { key: 'terrace', label: 'سناریو ب (تراسبندی)', hint: 'شیب کاهش‌یافته به ۵٪', slopePct: 5 },
];

/**
 * مقایسه کنارهم دو اجرای واقعی زنجیره علمی: پایه در برابر مداخله (تراسبندی).
 * هر دو اجرا با اقلیم/خاک واقعی (ERA5 + SoilGrids) انجام می‌شوند؛ تفاوت فقط پارامتر سناریو است.
 * نتایج، خروجی واقعی مدل‌ها هستند — نه داده ساختگی.
 */
export const ScenarioCompare: React.FC<ScenarioCompareProps> = ({ lat, lon, crop = 'wheat' }) => {
  const [results, setResults] = useState<Record<string, ScientificChainResult | null>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const [base, terrace] = await Promise.all([
        fetchScientificChain(lat, lon, { crop, plantingDate: '2024-11-15', slopePct: SCENARIOS[0].slopePct, catchmentKm2: 10, optimize: false }),
        fetchScientificChain(lat, lon, { crop, plantingDate: '2024-11-15', slopePct: SCENARIOS[1].slopePct, catchmentKm2: 10, optimize: false }),
      ]);
      setResults({ baseline: base, terrace });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در اجرای مقایسه سناریوها');
    } finally {
      setLoading(false);
    }
  };

  const metricOf = (r: ScientificChainResult | null, kind: 'erosion' | 'yield' | 'soc' | 'reliability'): number | null => {
    if (!r) return null;
    switch (kind) {
      case 'erosion': return r.erosion?.soil_loss_ton_ha_yr ?? null;
      case 'yield': return (r.aquacrop?.summary?.yield_ton_ha as number | undefined) ?? null;
      case 'soc': return (r.rothc?.summary?.soc_final_t_ha as number | undefined) ?? null;
      case 'reliability': return (r.water?.summary?.supply_reliability_pct as number | undefined) ?? null;
    }
  };

  const delta = (kind: 'erosion' | 'yield' | 'soc' | 'reliability') => {
    const a = metricOf(results.baseline, kind);
    const b = metricOf(results.terrace, kind);
    if (a == null || b == null) return null;
    if (kind === 'erosion') return ((b - a) / Math.max(Math.abs(a), 1e-9)) * 100; // کاهش = منفی (خوب)
    return ((b - a) / Math.max(Math.abs(a), 1e-9)) * 100;
  };

  const rows: { label: string; unit: string; kind: 'erosion' | 'yield' | 'soc' | 'reliability'; better: 'down' | 'up' }[] = [
    { label: 'فرسایش', unit: 't/ha/yr', kind: 'erosion', better: 'down' },
    { label: 'عملکرد گندم', unit: 't/ha', kind: 'yield', better: 'up' },
    { label: 'کربن خاک (SOC)', unit: 't/ha', kind: 'soc', better: 'up' },
    { label: 'قابلیت اطمینان آب', unit: '٪', kind: 'reliability', better: 'up' },
  ];

  const deltaChip = (kind: 'erosion' | 'yield' | 'soc' | 'reliability', better: 'down' | 'up') => {
    const d = delta(kind);
    if (d == null) return <span style={{ color: 'var(--color-text-secondary)' }}>—</span>;
    const good = better === 'down' ? d < 0 : d > 0;
    const Icon = d === 0 ? Minus : d > 0 ? ArrowUpRight : ArrowDownRight;
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontWeight: 700, color: good ? '#10b981' : '#f59e0b' }}>
        <Icon size={13} /> {Math.abs(d).toFixed(1)}٪
      </span>
    );
  };

  return (
    <div className="card" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.9rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.45rem', margin: 0 }}>
          <GitCompareArrows size={16} color="var(--color-primary)" /> مقایسه سناریوها
        </h3>
        <button
          onClick={() => void run()}
          disabled={loading}
          className="btn btn-secondary"
          style={{ padding: '0.4rem 0.9rem', borderRadius: 9, border: '1px solid var(--color-border)', cursor: 'pointer', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'var(--color-bg)' }}
        >
          <Play size={13} /> {loading ? 'در حال اجرای ۲ سناریو…' : 'مقایسه'}
        </button>
      </div>

      {error && <p style={{ color: '#ef4444', fontSize: '0.82rem', margin: '0 0 0.6rem' }}>{error}</p>}

      {results.baseline && results.terrace && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ color: 'var(--color-text-secondary)' }}>
              <th style={{ textAlign: 'right', padding: '0.3rem 0.4rem', borderBottom: '1px solid var(--color-border)' }}>شاخص</th>
              <th style={{ textAlign: 'center', padding: '0.3rem 0.4rem', borderBottom: '1px solid var(--color-border)' }}>{SCENARIOS[0].label}</th>
              <th style={{ textAlign: 'center', padding: '0.3rem 0.4rem', borderBottom: '1px solid var(--color-border)' }}>{SCENARIOS[1].label}</th>
              <th style={{ textAlign: 'center', padding: '0.3rem 0.4rem', borderBottom: '1px solid var(--color-border)' }}>تغییر</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const a = metricOf(results.baseline, row.kind);
              const b = metricOf(results.terrace, row.kind);
              return (
                <tr key={row.kind}>
                  <td style={{ padding: '0.35rem 0.4rem', borderBottom: '1px solid var(--color-border)' }}>{row.label}</td>
                  <td style={{ textAlign: 'center', padding: '0.35rem 0.4rem', borderBottom: '1px solid var(--color-border)', fontWeight: 600 }}>
                    {a != null ? `${a.toFixed(2)} ${row.unit}` : '—'}
                  </td>
                  <td style={{ textAlign: 'center', padding: '0.35rem 0.4rem', borderBottom: '1px solid var(--color-border)', fontWeight: 600, color: '#10b981' }}>
                    {b != null ? `${b.toFixed(2)} ${row.unit}` : '—'}
                  </td>
                  <td style={{ textAlign: 'center', padding: '0.35rem 0.4rem', borderBottom: '1px solid var(--color-border)' }}>
                    {deltaChip(row.kind, row.better)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {!results.baseline && !loading && !error && (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.82rem', margin: 0 }}>
          دو اجرای واقعی زنجیره (پایه در برابر تراسبندی) — تفاوت فقط در پارامتر شیب؛ بقیه داده‌ها یکسان و واقعی است.
        </p>
      )}
    </div>
  );
};
