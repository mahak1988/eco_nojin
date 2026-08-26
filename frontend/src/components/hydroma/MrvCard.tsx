import React, { useEffect, useRef, useState } from 'react';
import { Globe2, Play, Download, MapPin, FileText, Plus, X } from 'lucide-react';
import { Deck } from '@deck.gl/core';
import { ScatterplotLayer } from '@deck.gl/layers';

interface MrvCardProps {
  lat: number;
  lon: number;
}

interface MrvPayload {
  carbon?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  kobo?: Record<string, unknown>;
  rothc_chain_id?: string;
  error?: string;
}

/**
 * ماژول MRV کربن در داشبورد — محاسبه بودجه کربن با زنجیره واقعی (RothC) +
 * متدولوژی Verra VM0032 یا Gold Standard؛ داده میدانی اختیاری از KoboToolbox.
 * هیچ fallback ساختگی — خطا/وضعیت به‌صورت صادقانه.
 */
interface KoboSubmission {
  submission_id?: string | number;
  time?: string;
  soc_t_ha?: number;
  lat?: number | null;
  lon?: number | null;
}

/** نقشه نمونه‌برداری میدانی — deck.gl: نقاط واقعی KoboToolbox با رنگ SOC */
const FieldSampleMap: React.FC<{ samples: KoboSubmission[]; lat: number; lon: number }> = ({ samples, lat, lon }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const deckRef = useRef<Deck | null>(null);
  const pts = samples.filter((s) => s.lat != null && s.lon != null);

  useEffect(() => {
    if (!containerRef.current) return;
    const layer = new ScatterplotLayer({
      id: 'soc-samples',
      data: pts,
      getPosition: (d: KoboSubmission) => [d.lon as number, d.lat as number],
      getFillColor: (d: KoboSubmission) => {
        const v = d.soc_t_ha ?? 60;
        const t = Math.max(0, Math.min(1, (v - 50) / 25));
        return [Math.round(180 - 120 * t), Math.round(120 + 90 * t), 40, 220];
      },
      getRadius: 400,
      radiusUnits: 'meters',
      stroked: true,
      getLineColor: [255, 255, 255, 200],
      lineWidthMinPixels: 1,
    });
    deckRef.current = new Deck({
      parent: containerRef.current,
      initialViewState: { longitude: lon, latitude: lat, zoom: 11, pitch: 0 },
      controller: true,
      layers: [layer],
    });
    return () => {
      deckRef.current?.finalize();
      deckRef.current = null;
    };
  }, [lat, lon, pts.length]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ margin: '0.6rem 0' }}>
      <div ref={containerRef} style={{ width: '100%', height: 220, borderRadius: 12, overflow: 'hidden', background: '#0f172a', position: 'relative' }} />
      <p style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', margin: '0.3rem 0 0', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
        <MapPin size={11} /> {pts.length} نمونه میدانی KoboToolbox — رنگ = میزان SOC (t C/ha)
      </p>
    </div>
  );
};

const SAMPLE_CSV = `soc_t_ha,lat,lon,note
58.2,35.498,51.503,demo sample via API 1
61.4,35.507,51.495,demo sample via API 2
63.9,35.512,51.508,demo sample via API 3
65.2,35.494,51.511,demo sample via API 4
67.1,35.505,51.499,demo sample via API 5`;

interface PeriodRow {
  year: number;
  soc_t_ha: number;
  delta_tco2e_ha: number;
}

export const MrvCard: React.FC<MrvCardProps> = ({ lat, lon }) => {
  const [area, setArea] = useState(100);
  const [practice, setPractice] = useState('conservation_ag');
  const [methodology, setMethodology] = useState('vm0032');
  const [useSeries, setUseSeries] = useState(false);
  const [series, setSeries] = useState<{ year: number; soc: string }[]>([
    { year: 2020, soc: '63.0' },
    { year: 2025, soc: '63.7' },
  ]);
  const [result, setResult] = useState<MrvPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);

  const measurements = series
    .filter((r) => Number.isFinite(r.year) && r.soc.trim() !== '')
    .map((r) => ({ year: r.year, soc_t_ha: Number(r.soc) }));

  const buildBody = () =>
    JSON.stringify({
      lat,
      lon,
      crop: 'wheat',
      area_ha: area,
      practice,
      methodology,
      use_kobo: false,
      measurements: useSeries && measurements.length >= 2 ? measurements : [],
    });

  const run = async () => {
    setLoading(true);
    setResult(null);
    try {
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), 90_000);
      try {
        const res = await fetch('/api/mrv/carbon-budget', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: buildBody(),
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setResult((await res.json()) as MrvPayload);
      } finally {
        window.clearTimeout(timer);
      }
    } catch (err) {
      setResult({ error: err instanceof Error ? err.message : 'خطا' });
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async () => {
    setPdfBusy(true);
    try {
      const res = await fetch('/api/mrv/carbon-budget/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: buildBody(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mrv_carbon_budget_${methodology}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`دانلود گزارش ناموفق: ${err instanceof Error ? err.message : 'خطا'}`);
    } finally {
      setPdfBusy(false);
    }
  };

  const c = result?.carbon;
  const delta = typeof c?.delta_co2e_total === 'number' ? c.delta_co2e_total : null;
  const negative = delta != null && delta < 0;
  const mode = String(c?.data_mode ?? '—');
  const koboStatus = String((result?.kobo as Record<string, unknown> | undefined)?.status ?? 'skipped');
  const periods = (c?.periods as PeriodRow[] | undefined) ?? [];

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.9rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <Globe2 size={17} /> بودجه کربن — MRV
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          Verra VM0032 · Gold Standard SOC Framework · KoboToolbox
        </span>
      </div>

      <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '0.9rem' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          مساحت (ha)
          <input type="number" min="1" value={area} onChange={(e) => setArea(Number(e.target.value))} style={{ padding: '0.4rem 0.6rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)', width: 90 }} />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          مدیریت
          <select value={practice} onChange={(e) => setPractice(e.target.value)} style={{ padding: '0.4rem 0.6rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)' }}>
            <option value="conservation_ag">کشاورزی حفاظتی</option>
            <option value="agroforestry">آگروفارستری</option>
            <option value="none">بدون مداخله</option>
          </select>
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          استاندارد
          <select value={methodology} onChange={(e) => setMethodology(e.target.value)} style={{ padding: '0.4rem 0.6rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)', color: 'var(--color-text)' }}>
            <option value="vm0032">Verra VM0032</option>
            <option value="gold_standard">Gold Standard</option>
          </select>
        </label>
        <label style={{ display: 'flex', flexDirection: 'row', gap: '0.35rem', alignItems: 'center', fontSize: '0.76rem', color: 'var(--color-text-secondary)', paddingBottom: '0.45rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={useSeries} onChange={(e) => setUseSeries(e.target.checked)} />
          سری چنددوره‌ای t0→t5
        </label>
        <button onClick={() => void run()} disabled={loading} style={{ padding: '0.5rem 1.1rem', borderRadius: 10, border: 'none', cursor: 'pointer', background: 'var(--color-primary)', color: '#fff', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem' }}>
          <Play size={13} /> {loading ? 'در حال محاسبه…' : 'محاسبه'}
        </button>
      </div>

      {useSeries && (
        <div style={{ marginBottom: '0.9rem', padding: '0.6rem 0.8rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)', marginBottom: '0.4rem' }}>
            سال‌ها و SOC اندازه‌گیری‌شده (t C/ha) — حداقل ۲ نقطه برای روند؛ مقادیر نمونه را با داده آزمایشگاهی واقعی جایگزین کنید
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
            {series.map((row, i) => (
              <div key={i} style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                <input
                  type="number"
                  min="2000"
                  max="2100"
                  value={row.year}
                  onChange={(e) => setSeries((prev) => prev.map((r, j) => (j === i ? { ...r, year: Number(e.target.value) } : r)))}
                  style={{ padding: '0.35rem 0.45rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', width: 74 }}
                  title="سال"
                />
                <input
                  type="number"
                  step="0.1"
                  value={row.soc}
                  onChange={(e) => setSeries((prev) => prev.map((r, j) => (j === i ? { ...r, soc: e.target.value } : r)))}
                  style={{ padding: '0.35rem 0.45rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', width: 74 }}
                  title="SOC (t C/ha)"
                />
                <button
                  onClick={() => setSeries((prev) => prev.filter((_, j) => j !== i))}
                  disabled={series.length <= 2}
                  style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#ef4444', display: 'flex' }}
                  title="حذف"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
            <button
              onClick={() => setSeries((prev) => [...prev, { year: (prev[prev.length - 1]?.year ?? 2025) + 5, soc: prev[prev.length - 1]?.soc ?? '63.7' }])}
              disabled={series.length >= 6}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', border: '1px dashed var(--color-border)', background: 'transparent', borderRadius: 8, padding: '0.35rem 0.6rem', cursor: 'pointer', fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}
            >
              <Plus size={12} /> افزودن نقطه
            </button>
          </div>
        </div>
      )}

      {result?.error && <p style={{ color: '#ef4444', fontSize: '0.85rem', margin: '0 0 0.5rem' }}>⚠️ {result.error}</p>}

      {result && !result.error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '1.7rem', fontWeight: 800, color: negative ? '#ef4444' : '#10b981' }}>
              {delta != null ? `${delta > 0 ? '+' : ''}${delta.toFixed(1)} tCO2e` : '—'}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
              {negative ? 'افت کربن — مداخله لازم است' : 'ترسیب خالص'} · {mode}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(90px, 1fr))', gap: '0.4rem', flex: 1 }}>
            {[
              ['SOC اولیه', `${typeof c?.soc_initial_t_ha === 'number' ? c.soc_initial_t_ha.toFixed(1) : '—'} t C/ha`],
              ['SOC نهایی', `${typeof c?.soc_final_t_ha === 'number' ? c.soc_final_t_ha.toFixed(1) : '—'} t C/ha`],
              ['به ازای هکتار', `${typeof c?.delta_co2e_ha === 'number' ? c.delta_co2e_ha.toFixed(2) : '—'} tCO2e/ha`],
              ['Kobo', koboStatus],
            ].map(([k, v]) => (
              <div key={k} style={{ padding: '0.4rem 0.5rem', borderRadius: 8, background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
                <div style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)' }}>{k}</div>
                <div style={{ fontSize: '0.8rem', fontWeight: 700 }}>{v}</div>
              </div>
            ))}
          </div>
          <button
            onClick={() => void downloadPdf()}
            disabled={pdfBusy}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.5rem 0.9rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700, color: 'var(--color-text)' }}
          >
            <FileText size={14} /> {pdfBusy ? 'در حال ساخت…' : 'دانلود گزارش PDF'}
          </button>
        </div>
      )}

      {periods.length > 0 && (
        <div style={{ marginTop: '0.7rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.35rem' }}>📈 روند چنددوره‌ای (t0 → t5)</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.4rem' }}>
            {periods.map((p) => (
              <div key={p.year} style={{ padding: '0.45rem 0.6rem', borderRadius: 9, border: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
                <div style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)' }}>{p.year} · Δ {p.delta_tco2e_ha > 0 ? '+' : ''}{p.delta_tco2e_ha.toFixed(1)} tCO2e/ha</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: p.delta_tco2e_ha >= 0 ? '#10b981' : '#ef4444' }}>{p.soc_t_ha} t C/ha</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* نمونه‌های میدانی KoboToolbox + نقشه deck.gl + راهنمای import */}
      {result && !result.error && (() => {
        const subs = ((result?.kobo as Record<string, unknown> | undefined)?.submissions as KoboSubmission[] | undefined) ?? [];
        if (subs.length > 0) {
          return <FieldSampleMap samples={subs} lat={lat} lon={lon} />;
        }
        const koboStatusFull = String((result?.kobo as Record<string, unknown> | undefined)?.status ?? 'skipped');
        return (
          <div style={{ marginTop: '0.6rem', padding: '0.7rem 0.9rem', borderRadius: 10, background: 'var(--color-bg)', border: '1px dashed var(--color-border)' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.3rem' }}>📋 فعال‌سازی نمونه‌های میدانی (وضعیت Kobo: {koboStatusFull})</div>
            <ol style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)', margin: '0 0 0.5rem', paddingInlineStart: '1.1rem', lineHeight: 1.8 }}>
              <li>در kf.kobotoolbox.org فرم «Eco Nojin SOC samples» (ساخته‌شده) را باز کنید</li>
              <li>Data ← Import ← فایل CSV زیر را بکشید (ستون‌ها: soc_t_ha, lat, lon, note)</li>
              <li>دوباره «محاسبه» بزنید — حالت به field_verified تغییر می‌کند و نقشه نمونه‌ها فعال می‌شود</li>
            </ol>
            <button
              onClick={() => {
                const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'kobo_soc_samples.csv';
                a.click();
                URL.revokeObjectURL(url);
              }}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', padding: '0.4rem 0.9rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', fontSize: '0.76rem', fontWeight: 700 }}
            >
              <Download size={13} /> دریافت CSV ۵ نمونه (demo)
            </button>
          </div>
        );
      })()}

      {!result && !loading && (
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>
          برآورد بر پایه زنجیره واقعی RothC (ERA5 + SoilGrids)؛ برای «تأیید میدانی»، حساب رایگان KoboToolbox بسازید (راهنما در docs/fa/40) — گواهی استاندارد نیازمند ثبت در رجیستری رسمی است.
        </p>
      )}
    </div>
  );
};
