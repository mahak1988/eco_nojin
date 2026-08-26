import React, { useState } from 'react';
import { Play, Mountain, Waves, Sprout, Droplets, Cpu, Database, CheckCircle2, AlertTriangle } from 'lucide-react';
import { fetchScientificChain } from '../../services/scientificChainApi';
import type { ScientificChainResult } from '../../types/vll';

interface ScientificChainPanelProps {
  lat: number;
  lon: number;
  crop?: string;
  plantingDate?: string;
  slopePct?: number;
  catchmentKm2?: number;
  onResult?: (result: ScientificChainResult) => void;
}

interface Metric {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
}

const statusColor = (status?: string) =>
  status === 'ok' || status === 'completed' || status === 'prep_ready'
    ? 'var(--color-success, #10b981)'
    : status === 'failed'
      ? '#ef4444'
      : '#f59e0b';

/**
 * پنل «زنجیره علمی واقعی» — اجرای RUSLE ← SWAT+ ← Pywr ← RothC ← AquaCrop ← HEC-RAS ← NSGA-II
 * روی بک‌اند. وضعیت هر موتور به‌صورت صادقانه نمایش داده می‌شود (نیاز به باینری/اعتبارنامه = زرد).
 */
export const ScientificChainPanel: React.FC<ScientificChainPanelProps> = ({
  lat,
  lon,
  crop = 'wheat',
  plantingDate = '2024-11-15',
  slopePct = 10,
  catchmentKm2 = 10,
  onResult,
}) => {
  const [result, setResult] = useState<ScientificChainResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScientificChain(lat, lon, {
        crop,
        plantingDate,
        slopePct,
        catchmentKm2,
        optimize: true,
      });
      setResult(data);
      onResult?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در اجرای زنجیره علمی');
    } finally {
      setLoading(false);
    }
  };

  const s = (block?: { status?: string; summary?: Record<string, unknown>; error?: string | null }) => ({
    status: block?.status,
    summary: block?.summary ?? {},
    error: block?.error ?? null,
  });

  const erosion = result?.erosion;
  const rothc = s(result?.rothc);
  const aquacrop = s(result?.aquacrop);
  const water = s(result?.water);
  const flood = s(result?.flood);
  const swat = s(result?.swat);
  const opt = s(result?.optimization);

  const metrics: Metric[] = [
    {
      icon: <Mountain size={18} color="#f59e0b" />,
      label: 'فرسایش (RUSLE)',
      value: erosion?.soil_loss_ton_ha_yr != null ? `${erosion.soil_loss_ton_ha_yr.toFixed(2)} t/ha/yr` : '—',
      hint: erosion?.risk ? `ریسک: ${erosion.risk}` : undefined,
    },
    {
      icon: <Sprout size={18} color="#10b981" />,
      label: 'کربن خاک (RothC)',
      value: (rothc.summary.soc_final_t_ha as number | undefined) != null ? `${Number(rothc.summary.soc_final_t_ha).toFixed(1)} t/ha` : '—',
      hint: (rothc.summary.soc_change_t_ha_yr as number | undefined) != null ? `تغییر: ${Number(rothc.summary.soc_change_t_ha_yr).toFixed(3)} t/ha/yr` : undefined,
    },
    {
      icon: <Droplets size={18} color="#3b82f6" />,
      label: 'عملکرد گندم (AquaCrop)',
      value: (aquacrop.summary.yield_ton_ha as number | undefined) != null ? `${Number(aquacrop.summary.yield_ton_ha).toFixed(2)} t/ha` : '—',
      hint: aquacrop.status === 'ok' ? `برداشت: ${String(aquacrop.summary.harvest_date ?? '—')}` : undefined,
    },
    {
      icon: <Waves size={18} color="#06b6d4" />,
      label: 'تخصیص آب (Pywr)',
      value: (water.summary.supply_reliability_pct as number | undefined) != null ? `${Number(water.summary.supply_reliability_pct).toFixed(1)}٪` : '—',
      hint: (water.summary.total_deficit_mcm as number | undefined) != null ? `کسری: ${Number(water.summary.total_deficit_mcm).toFixed(2)} MCM` : undefined,
    },
    {
      icon: <Waves size={18} color="#8b5cf6" />,
      label: 'سیلاب (HEC-RAS)',
      value: (flood.summary.wse_m as number | undefined) != null ? `${Number(flood.summary.wse_m).toFixed(2)} m` : '—',
      hint: String(flood.summary.engine ?? flood.status ?? '—'),
    },
    {
      icon: <Cpu size={18} color="#ec4899" />,
      label: 'بهینه‌سازی (NSGA-II)',
      value: (opt.summary.pareto_size as number | undefined) != null ? `${Number(opt.summary.pareto_size)} راه‌حل` : '—',
      hint: (opt.summary.best_yield_t_ha as number | undefined) != null ? `بهترین عملکرد: ${Number(opt.summary.best_yield_t_ha).toFixed(2)} t/ha` : undefined,
    },
  ];

  const chips = [
    { name: 'SWAT+', status: swat.status ?? '—', note: swat.status === 'prep_ready' ? 'آماده، نیاز به باینری' : undefined },
    { name: 'Pywr', status: water.status ?? '—' },
    { name: 'HEC-RAS', status: flood.status ?? '—' },
    { name: 'RothC', status: rothc.status ?? '—' },
    { name: 'AquaCrop', status: aquacrop.status ?? '—' },
    { name: 'NSGA-II', status: opt.status ?? '—' },
  ];

  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Database size={18} color="var(--color-primary)" /> زنجیره علمی واقعی
        </h3>
        <button
          onClick={() => void run()}
          disabled={loading}
          className="btn btn-primary"
          style={{ padding: '0.5rem 1.25rem', borderRadius: 10, border: 'none', cursor: 'pointer', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}
        >
          <Play size={14} /> {loading ? 'در حال اجرا…' : result ? 'اجرای دوباره' : 'اجرای زنجیره'}
        </button>
      </div>

      {error && <p style={{ color: '#ef4444', fontSize: '0.9rem', marginBottom: '0.75rem' }}>{error}</p>}
      {loading && <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>اجرای ۶ موتور علمی — معمولاً ۳ تا ۸ ثانیه (اولین بار)…</p>}

      {result && (
        <>
          {result.cache_hit && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.75rem', fontSize: '0.8rem', color: 'var(--color-success, #10b981)' }}>
              <CheckCircle2 size={14} /> نتیجه از کش بازیابی شد (شناسه: {result.chain_id.slice(0, 8)})
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.6rem', marginBottom: '1rem' }}>
            {metrics.map((m) => (
              <div key={m.label} className="stat-mini">
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>{m.icon} {m.label}</span>
                <strong>{m.value}</strong>
                {m.hint && <small style={{ color: 'var(--color-text-secondary)', fontSize: '0.72rem' }}>{m.hint}</small>}
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {chips.map((c) => (
              <span
                key={c.name}
                title={c.note ?? c.status}
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                  padding: '0.25rem 0.6rem', borderRadius: 999, fontSize: '0.75rem',
                  background: 'var(--color-bg)', border: '1px solid var(--color-border)',
                  color: 'var(--color-text-secondary)',
                }}
              >
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor(c.status) }} />
                {c.name}: {c.status}
                {c.status === 'requires_hecras_install' && <AlertTriangle size={12} />}
              </span>
            ))}
          </div>
        </>
      )}

      {!result && !loading && (
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem', margin: 0 }}>
          RUSLE ← SWAT+ ← Pywr ← RothC ← AquaCrop ← HEC-RAS ← NSGA-II — همه با داده واقعی اقلیم و خاک. وضعیت‌های «نیاز به باینری/اعتبارنامه» صادقانه نمایش داده می‌شوند.
        </p>
      )}

      <style>{`
        .stat-mini { display: flex; flex-direction: column; gap: 0.25rem; padding: 0.75rem; border-radius: 12px; background: var(--color-bg); border: 1px solid var(--color-border); font-size: 0.8rem; color: var(--color-text-secondary); }
        .stat-mini strong { font-size: 1rem; color: var(--color-text); }
      `}</style>
    </div>
  );
};
