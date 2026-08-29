import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, Mountain, Leaf, Sprout, Waves, CloudRain as FloodIcon, Cpu, Database, Play, RefreshCw, Globe2,
} from 'lucide-react';
import { Card } from '../ui';
import './scientific.css';
import { fetchScientificChain } from '../../services/scientificChainApi';
import type { ScientificChainResult } from '../../types/vll';

// deck.gl نقشه سیلاب — lazy تا باندل ورودی کوچک بماند
const FloodZoneMap = React.lazy(() => import('./FloodZoneMap').then((m) => ({ default: m.FloodZoneMap })));

interface HubState {
  lat: number;
  lon: number;
  crop: string;
  slopePct: number;
  catchmentKm2: number;
}

const DEFAULT_STATE: HubState = { lat: 35.5, lon: 51.5, crop: 'wheat', slopePct: 10, catchmentKm2: 10 };

const statusBadge = (status?: string) => {
  const ok = status === 'ok' || status === 'completed' || status === 'prep_ready';
  const fail = status === 'failed';
  return (
    <span
      style={{
        display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
        padding: '0.2rem 0.6rem', borderRadius: 999, fontSize: '0.72rem', fontWeight: 700,
        background: fail ? 'rgba(239,68,68,0.12)' : ok ? 'rgba(16,185,129,0.12)' : 'rgba(245,158,11,0.12)',
        color: fail ? '#ef4444' : ok ? '#10b981' : '#f59e0b',
      }}
    >
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: fail ? '#ef4444' : ok ? '#10b981' : '#f59e0b' }} />
      {status ?? '—'}
    </span>
  );
};

const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

const Field: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="sci-field">
    <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>{label}</div>
    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{value}</div>
  </div>
);

/**
 * مرکز شبیه‌سازهای علمی واقعی — جایگزین صفحات ناقص/نمایشی قدیمی /simulator.
 * همه خروجی‌ها از زنجیره واقعی (RUSLE ← SWAT+ ← Pywr ← RothC ← AquaCrop ← HEC-RAS ← NSGA-II) می‌آیند؛
 * هیچ fallback ساختگی وجود ندارد — مقادیر غایب به‌صورت «—» و وضعیت‌ها صادقانه نمایش داده می‌شوند.
 */
export const ScientificHub: React.FC = () => {
  const [state, setState] = useState<HubState>(DEFAULT_STATE);
  const [result, setResult] = useState<ScientificChainResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState('overview');
  const [mrv, setMrv] = useState<Record<string, unknown> | null>(null);
  const [mrvLoading, setMrvLoading] = useState(false);
  const [mrvArea, setMrvArea] = useState(100);
  const [mrvPractice, setMrvPractice] = useState('conservation_ag');

  const runMrv = useCallback(async () => {
    setMrvLoading(true);
    setMrv(null);
    try {
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), 90_000);
      try {
        const res = await fetch('/api/mrv/carbon-budget', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lat: state.lat, lon: state.lon, crop: state.crop,
            area_ha: mrvArea, practice: mrvPractice, use_kobo: false,
          }),
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setMrv((await res.json()) as Record<string, unknown>);
      } finally {
        window.clearTimeout(timer);
      }
    } catch (err) {
      setMrv({ error: err instanceof Error ? err.message : 'خطا' });
    } finally {
      setMrvLoading(false);
    }
  }, [state.lat, state.lon, state.crop, mrvArea, mrvPractice]);

  const run = useCallback(async (s: HubState) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScientificChain(s.lat, s.lon, {
        crop: s.crop,
        plantingDate: '2024-11-15',
        slopePct: s.slopePct,
        catchmentKm2: s.catchmentKm2,
        optimize: true,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در اجرای زنجیره علمی');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void run(DEFAULT_STATE);
  }, [run]);

  const r = result;
  const erosion = r?.erosion;
  const rothc = r?.rothc;
  const aquacrop = r?.aquacrop;
  const water = r?.water;
  const flood = r?.flood;
  const opt = r?.optimization;
  const swat = r?.swat;

  const rothcPools = (rothc?.outputs?.pools as Record<string, number> | undefined) ?? null;
  const socSeries = (rothc?.outputs?.annual_series as number[] | undefined) ?? [];
  const supplySeries = (water?.outputs?.supply_series as number[] | undefined) ?? [];
  const storageSeries = (water?.outputs?.storage_series as number[] | undefined) ?? [];

  const tabs = useMemo(
    () => [
      {
        id: 'overview',
        label: 'نمای کلی',
        icon: <Activity size={15} />,
        content: (
          <div>
            <div className="sci-grid">
              <Card title="فرسایش (RUSLE)" icon={<Mountain size={18} />}>
                <div className="sci-bignum">{erosion?.soil_loss_ton_ha_yr?.toFixed(2) ?? '—'} <small style={{ fontSize: '0.8rem', fontWeight: 400 }}>t/ha/yr</small></div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>ریسک: {erosion?.risk ?? '—'}</div>
              </Card>
              <Card title="کربن خاک (RothC)" icon={<Leaf size={18} />}>
                <div className="sci-bignum">{num(rothc?.summary?.soc_final_t_ha)?.toFixed(1) ?? '—'} <small style={{ fontSize: '0.8rem', fontWeight: 400 }}>t/ha</small></div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>تغییر: {num(rothc?.summary?.soc_change_t_ha_yr)?.toFixed(3) ?? '—'} t/ha/yr</div>
              </Card>
              <Card title="عملکرد گندم (AquaCrop)" icon={<Sprout size={18} />}>
                <div className="sci-bignum">{num(aquacrop?.summary?.yield_ton_ha)?.toFixed(2) ?? '—'} <small style={{ fontSize: '0.8rem', fontWeight: 400 }}>t/ha</small></div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>آبیاری: {num(aquacrop?.summary?.irrigation_mm)?.toFixed(0) ?? '—'} mm</div>
              </Card>
              <Card title="تخصیص آب (Pywr)" icon={<Waves size={18} />}>
                <div className="sci-bignum">{num(water?.summary?.supply_reliability_pct)?.toFixed(1) ?? '—'} <small style={{ fontSize: '0.8rem', fontWeight: 400 }}>٪</small></div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>کسری: {num(water?.summary?.total_deficit_mcm)?.toFixed(2) ?? '—'} MCM</div>
              </Card>
            </div>
            {r?.calibration?.status === 'no_observed_data' && (
              <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
                📊 کالیبراسیون: {String(r.calibration.status)} — پس از فراهم‌شدن سری مشاهداتی، KGE محاسبه می‌شود (هدف ≥ ۰.۵۵).
              </p>
            )}
          </div>
        ),
      },
      {
        id: 'erosion',
        label: 'فرسایش',
        icon: <Mountain size={15} />,
        content: (
          <Card title="فرسایش خاک — RUSLE (واقعی)" icon={<Mountain size={18} />}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
              {[
                ['فرسایش سالانه', `${erosion?.soil_loss_ton_ha_yr?.toFixed(2) ?? '—'} t/ha/yr`],
                ['ضریب R (باران)', String(erosion?.r_factor ?? '—')],
                ['ضریب K (خاک)', String(erosion?.k_factor ?? '—')],
                ['ضریب LS (شیب)', String(erosion?.ls_factor ?? '—')],
                ['ضریب C (پوشش)', String(erosion?.c_factor ?? '—')],
                ['ضریب P (مدیریت)', String(erosion?.p_factor ?? '—')],
              ].map(([k, v]) => (
                <div key={k} className="sci-metric">
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>{k}</div>
                  <div style={{ fontWeight: 700, fontSize: '1rem' }}>{v}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              فرمول جهانی هدررفت خاک (USLE/RUSLE) با ورودی‌های واقعی: باران (ERA5)، ضریب K از بافت خاک SoilGrids، شیب از DEM.
            </p>
          </Card>
        ),
      },
      {
        id: 'carbon',
        label: 'کربن',
        icon: <Leaf size={15} />,
        content: (
          <Card title="کربن آلی خاک — RothC-26.3 (pyRothC واقعی)" icon={<Leaf size={18} />}>
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '2rem', fontWeight: 800 }}>{num(rothc?.summary?.soc_final_t_ha)?.toFixed(1) ?? '—'} <small style={{ fontSize: '0.9rem', fontWeight: 400 }}>t C/ha</small></div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>
                  اولیه: {num(rothc?.outputs?.initial_soc_t_ha)?.toFixed(1) ?? '—'} → نهایی: {num(rothc?.summary?.soc_final_t_ha)?.toFixed(1) ?? '—'} ({num(rothc?.summary?.soc_change_t_ha_yr)?.toFixed(3) ?? '—'} t/ha/yr)
                </div>
              </div>
              {rothcPools && (
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {Object.entries(rothcPools).map(([pool, v]) => (
                    <div key={pool} className="sci-metric">
                      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>{pool}</div>
                      <div style={{ fontWeight: 700 }}>{v.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            {socSeries.length > 1 && (
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 90 }}>
                {socSeries.map((v, i) => (
                  <div
                    key={i}
                    title={`سال ${i + 1}: ${v.toFixed(1)} t/ha`}
                    style={{
                      flex: 1,
                      height: `${((v - Math.min(...socSeries)) / Math.max(1e-6, Math.max(...socSeries) - Math.min(...socSeries))) * 100}%`,
                      background: 'linear-gradient(180deg, #10b981, #059669)',
                      borderRadius: '2px 2px 0 0',
                      minHeight: 2,
                    }}
                  />
                ))}
              </div>
            )}
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}>
              موتور: {String(rothc?.outputs?.engine ?? 'pyRothC')} · استخرهای DPM/RPM/BIO/HUM/IOM · ورودی اقلیم/رس واقعی.
            </p>
          </Card>
        ),
      },
      {
        id: 'crop',
        label: 'محصول',
        icon: <Sprout size={15} />,
        content: (
          <Card title="عملکرد محصول — AquaCrop-OSPy (واقعی)" icon={<Sprout size={18} />}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
              {[
                ['عملکرد دانه', `${num(aquacrop?.summary?.yield_ton_ha)?.toFixed(2) ?? '—'} t/ha`],
                ['زی‌توده', `${num(aquacrop?.outputs?.biomass_ton_ha)?.toFixed(2) ?? '—'} t/ha`],
                ['آبیاری فصلی', `${num(aquacrop?.summary?.irrigation_mm)?.toFixed(1) ?? '—'} mm`],
                ['بهره‌وری آب', `${num(aquacrop?.outputs?.water_productivity_kg_m3)?.toFixed(2) ?? '—'} kg/m³`],
                ['تاریخ برداشت', String(aquacrop?.outputs?.harvest_date ?? '—')],
              ].map(([k, v]) => (
                <div key={k} className="sci-metric">
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>{k}</div>
                  <div style={{ fontWeight: 700, fontSize: '1rem' }}>{v}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              محصول: {state.crop} · تاریخ کاشت ۲۰۲۴-۱۱-۱۵ · آب‌وهوای روزانه واقعی (ERA5) + بافت خاک واقعی (SoilGrids).
            </p>
          </Card>
        ),
      },
      {
        id: 'water',
        label: 'آب',
        icon: <Waves size={15} />,
        content: (
          <Card title="تخصیص آب حوضه — Pywr (واقعی)" icon={<Waves size={18} />}>
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '2rem', fontWeight: 800 }}>{num(water?.summary?.supply_reliability_pct)?.toFixed(1) ?? '—'} <small style={{ fontSize: '0.9rem', fontWeight: 400 }}>٪ قابلیت اطمینان</small></div>
                <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem' }}>کسری کل: {num(water?.summary?.total_deficit_mcm)?.toFixed(2) ?? '—'} MCM</div>
              </div>
            </div>
            {supplySeries.length > 0 && (
              <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', marginBottom: '0.3rem' }}>تأمین ماهانه (MCM)</div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 70 }}>
                  {supplySeries.map((v, i) => (
                    <div key={i} title={`ماه ${i + 1}: ${v.toFixed(3)}`} style={{ flex: 1, height: `${Math.min(100, (v / Math.max(1e-6, Math.max(...supplySeries))) * 100)}%`, background: '#3b82f6', borderRadius: '2px 2px 0 0', minHeight: 2 }} />
                  ))}
                </div>
              </div>
            )}
            {storageSeries.length > 0 && (
              <div>
                <div style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', marginBottom: '0.3rem' }}>ذخیره مخزن ماهانه (MCM)</div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 70 }}>
                  {storageSeries.map((v, i) => (
                    <div key={i} title={`ماه ${i + 1}: ${v.toFixed(3)}`} style={{ flex: 1, height: `${Math.min(100, (v / Math.max(1e-6, Math.max(...storageSeries))) * 100)}%`, background: '#06b6d4', borderRadius: '2px 2px 0 0', minHeight: 2 }} />
                  ))}
                </div>
              </div>
            )}
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}>
              شبکه: ورودی (رواناب) ← مخزن ← تقاضای کشاورزی + نیاز محیط‌زیست · گام ماهانه · موتور: pywr 1.31.
            </p>
          </Card>
        ),
      },
      {
        id: 'flood',
        label: 'سیلاب',
        icon: <FloodIcon size={15} />,
        content: (
          <Card title="سیلاب — HEC-RAS (خودکارسازی) + نقشه deck.gl" icon={<FloodIcon size={18} />}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              {statusBadge(flood?.status)}
              <span style={{ fontSize: '0.85rem' }}>
                ارتفاع آب (تقریبی Manning): <strong>{num(flood?.summary?.wse_m)?.toFixed(2) ?? '—'} m</strong>
              </span>
              {flood?.summary?.requires_hecras_install === true && (
                <a
                  href="https://www.hec.usace.army.mil/software/hec-ras/download.aspx"
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }}
                >
                  دانلود رایگان HEC-RAS (USACE)
                </a>
              )}
            </div>
            <React.Suspense fallback={<div style={{ height: 360, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>در حال بارگذاری نقشه…</div>}>
              <FloodZoneMap
                lat={state.lat}
                lon={state.lon}
                floodCells={[]}
                floodStatus={flood?.status}
                floodEngine={String(flood?.summary?.engine ?? '—')}
                floodWseM={num(flood?.summary?.wse_m) ?? undefined}
                requiresHecrasInstall={flood?.summary?.requires_hecras_install === true}
              />
            </React.Suspense>
          </Card>
        ),
      },
      {
        id: 'opt',
        label: 'بهینه‌سازی',
        icon: <Cpu size={15} />,
        content: (
          <Card title="بهینه‌سازی چندهدفه — NSGA-II (pymoo)" icon={<Cpu size={18} />}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
              {[
                ['وضعیت', String(opt?.status ?? '—')],
                ['حالت', String(opt?.summary?.mode ?? '—')],
                ['راه‌حل‌های پارتو', String(opt?.summary?.pareto_size ?? '—')],
                ['بهترین عملکرد', `${num(opt?.summary?.best_yield_t_ha)?.toFixed(2) ?? '—'} t/ha`],
                ['کمترین فرسایش', `${num(opt?.summary?.min_erosion_t_ha_yr)?.toFixed(2) ?? '—'} t/ha/yr`],
              ].map(([k, v]) => (
                <div key={k} className="sci-metric">
                  <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>{k}</div>
                  <div style={{ fontWeight: 700, fontSize: '1rem' }}>{v}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              ۴ هدف: کاهش فرسایش، کاهش کسری آب، افزایش عملکرد، افزایش SOC · سوروگیت لنگرشده به خروجی‌های واقعی زنجیره (برچسب صادقانه).
            </p>
          </Card>
        ),
      },
      {
        id: 'swat',
        label: 'SWAT+',
        icon: <Database size={15} />,
        content: (
          <Card title="SWAT+ — آماده‌سازی پروژه (pySWATPlus)" icon={<Database size={18} />}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              {statusBadge(swat?.status)}
              {swat?.summary?.run_requires_executable === true && (
                <>
                  <span style={{ fontSize: '0.85rem' }}>اجرای کامل نیازمند باینری رایگان SWAT+ است:</span>
                  <a href="https://swat.tamu.edu/software/plus/" target="_blank" rel="noreferrer" style={{ fontSize: '0.8rem', color: 'var(--color-primary)' }}>
                    دانلود رایگان SWAT+ (swat.tamu.edu)
                  </a>
                </>
              )}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              پروژه با ورودی‌های واقعی آماده شده: اقلیم ERA5 (بارش/دما/ET0 روزانه)، خاک SoilGrids، کاربرد اراضی و توپوگرافی حوزه ({state.catchmentKm2} km²).
            </p>
          </Card>
        ),
      },
      {
        id: 'mrv',
        label: 'MRV کربن',
        icon: <Globe2 size={15} />,
        content: (
          <Card title="حسابداری کربن — MRV (Verra VM0032 + KoboToolbox)" icon={<Globe2 size={18} />}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '1rem' }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                مساحت (هکتار)
                <input type="number" min="1" value={mrvArea} onChange={(e) => setMrvArea(Number(e.target.value))} style={{ padding: '0.45rem 0.7rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)', width: 110 }} />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                مدیریت
                <select value={mrvPractice} onChange={(e) => setMrvPractice(e.target.value)} style={{ padding: '0.45rem 0.7rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)', width: 150 }}>
                  <option value="conservation_ag">کشاورزی حفاظتی</option>
                  <option value="agroforestry">آگروفارستری</option>
                  <option value="none">بدون مداخله</option>
                </select>
              </label>
              <button onClick={() => void runMrv()} disabled={mrvLoading} className="btn btn-primary" style={{ padding: '0.55rem 1.2rem', borderRadius: 10, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}>
                <Play size={14} /> {mrvLoading ? 'در حال محاسبه…' : 'محاسبه بودجه کربن'}
              </button>
            </div>

            {mrv && typeof mrv.error === 'string' && mrv.error ? <p style={{ color: '#ef4444', fontSize: '0.85rem' }}>⚠️ {mrv.error}</p> : null}

            {mrv && !mrv.error && (() => {
              const c = (mrv.carbon ?? {}) as Record<string, unknown>;
              const s = (mrv.summary ?? {}) as Record<string, unknown>;
              const kobo = (mrv.kobo ?? {}) as Record<string, unknown>;
              const delta = typeof c.delta_co2e_total === 'number' ? c.delta_co2e_total : null;
              const mode = String(c.data_mode ?? '—');
              const negative = delta != null && delta < 0;
              return (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.7rem', marginBottom: '0.9rem', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '1.9rem', fontWeight: 800, color: negative ? '#ef4444' : '#10b981' }}>
                      {delta != null ? `${delta > 0 ? '+' : ''}${delta.toFixed(1)} tCO2e` : '—'}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)' }}>
                      {negative ? 'افت کربن (سناریوی پایه در حال انتشار است — مداخله لازم)' : 'ترسیب کربن خالص'}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem', marginBottom: '0.9rem' }}>
                    <Field label="SOC اولیه" value={`${typeof c.soc_initial_t_ha === 'number' ? c.soc_initial_t_ha.toFixed(1) : '—'} t C/ha`} />
                    <Field label="SOC نهایی" value={`${typeof c.soc_final_t_ha === 'number' ? c.soc_final_t_ha.toFixed(1) : '—'} t C/ha`} />
                    <Field label="تغییر سالانه" value={`${typeof c.delta_soc_t_ha_yr === 'number' ? c.delta_soc_t_ha_yr.toFixed(3) : '—'} t C/ha`} />
                    <Field label="به ازای هکتار" value={`${typeof c.delta_co2e_ha === 'number' ? c.delta_co2e_ha.toFixed(2) : '—'} tCO2e/ha`} />
                    <Field label="مساحت" value={`${typeof c.area_ha === 'number' ? c.area_ha : '—'} ha`} />
                    <Field label="حالت داده" value={mode} />
                    <Field label="وضعیت" value={String(s.status ?? '—')} />
                    <Field label="ضریب ماندگاری" value={String(c.permanence_factor ?? '—')} />
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: '0 0 0.4rem' }}>
                    متد: {String(c.methodology ?? '—')} · تبدیل IPCC (×3.667) · زنجیره RothC: {String(mrv.rothc_chain_id ?? '—').slice(0, 8)}
                  </p>
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>
                    KoboToolbox: {String(kobo.status ?? 'skipped')}{kobo.status === 'requires_credentials' ? ' — با افزودن KOBO_TOKEN/KOBO_FORM_ID به .env، نمونه‌های میدانی SOC خوانده می‌شوند' : ''}
                  </p>
                </div>
              );
            })()}

            {!mrv && !mrvLoading && (
              <p style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)', margin: 0 }}>
                بودجه کربن خاک بر اساس زنجیره واقعی (RothC-26.3 با ERA5/SoilGrids) + داده میدانی اختیاری KoboToolbox؛ خروجی برآورد مدل است و گواهی Verra/Gold Standard نیازمند مستندات کامل متدولوژی است.
              </p>
            )}
          </Card>
        ),
      },
    ],
    [r, erosion, rothc, aquacrop, water, flood, opt, swat, rothcPools, socSeries, supplySeries, storageSeries, state.catchmentKm2, state.crop, state.lat, state.lon, mrv, mrvLoading, mrvArea, mrvPractice, runMrv],
  );

  return (
    <div className="sci-root">
      {/* Input bar */}
      <div className="sci-inputbar">
        {(
          [
            ['lat', 'عرض جغرافیایی', state.lat],
            ['lon', 'طول جغرافیایی', state.lon],
            ['slopePct', 'شیب (٪)', state.slopePct],
            ['catchmentKm2', 'مساحت حوزه (km²)', state.catchmentKm2],
          ] as const
        ).map(([key, label, value]) => (
          <label key={key} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
            {label}
            <input
              type="number"
              step="0.1"
              value={value}
              onChange={(e) => setState((s) => ({ ...s, [key]: Number(e.target.value) }))}
              style={{ padding: '0.45rem 0.7rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)', width: 130 }}
            />
          </label>
        ))}
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
          محصول
          <select
            value={state.crop}
            onChange={(e) => setState((s) => ({ ...s, crop: e.target.value }))}
            style={{ padding: '0.45rem 0.7rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)', width: 130 }}
          >
            <option value="wheat">گندم</option>
            <option value="maize">ذرت</option>
            <option value="barley">جو</option>
          </select>
        </label>
        <button
          onClick={() => void run(state)}
          disabled={loading}
          className="btn btn-primary"
          style={{ padding: '0.55rem 1.4rem', borderRadius: 10, border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.4rem', fontWeight: 600 }}
        >
          {loading ? <><RefreshCw size={15} className="hub-spin" /> در حال اجرا…</> : <><Play size={15} /> اجرای زنجیره</>}
        </button>
        {r?.cache_hit && (
          <span style={{ fontSize: '0.75rem', color: 'var(--color-success, #10b981)' }}>⚡ نتیجه از کش (شناسه: {r.chain_id.slice(0, 8)})</span>
        )}
      </div>

      {error && <p style={{ color: '#ef4444', fontSize: '0.9rem', marginBottom: '1rem' }}>⚠️ {error}</p>}

      {/* Tabs */}
      <div className="sci-tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.5rem 1rem', borderRadius: 999, cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
              border: tab === t.id ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
              background: tab === t.id ? 'color-mix(in srgb, var(--color-primary) 12%, transparent)' : 'var(--color-surface)',
              color: tab === t.id ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            }}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {tabs.find((t) => t.id === tab)?.content}

      <style>{`@keyframes hub-spin { to { transform: rotate(360deg); } } .hub-spin { animation: hub-spin 1s linear infinite; }`}</style>
    </div>
  );
};
