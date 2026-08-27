import React, { useEffect, useMemo, useState } from 'react';
import { Droplets, AlertTriangle, RefreshCw } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

interface SeriesPoint {
  month?: string;
  spi?: number | null;
  spei?: number | null;
  precip_mm?: number;
}

interface DroughtData {
  status?: string;
  latest?: { month?: string; spi?: number | null; spi_class?: { label?: string; level?: string }; spei?: number | null };
  summary?: { months_below_minus1?: number; worst_spi?: number | null };
  alert?: { level?: string };
  months_total?: number;
  series?: SeriesPoint[];
  note?: string;
  error?: string;
}

const LEVEL_COLOR: Record<string, string> = {
  none: '#10b981',
  mild: '#f59e0b',
  moderate: '#f97316',
  severe: '#ef4444',
  extreme: '#7f1d1d',
  unknown: '#94a3b8',
};

/**
 * فاز ۸-ب — پایش خشکسالی SPI/SPEI با داده واقعی ERA5 (رایگان):
 * نمودار سری شاخص‌ها + طبقه‌بندی WMO + هشدار اولیه.
 */
export const DroughtCard: React.FC = () => {
  const [lat, setLat] = useState(35.7);
  const [lon, setLon] = useState(51.4);
  const [months, setMonths] = useState(6);
  const [data, setData] = useState<DroughtData | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle');

  const run = async () => {
    setStatus('loading');
    try {
      const res = await fetch('/api/v1/motors/drought', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lon, timescale_months: months }),
      });
      const d = (await res.json()) as DroughtData;
      if (d.status === 'ok') {
        setData(d);
        setStatus('ok');
      } else {
        setStatus('error');
        setData({ error: String(d.error ?? 'خطا') });
      }
    } catch (e) {
      setStatus('error');
      setData({ error: e instanceof Error ? e.message : 'خطا' });
    }
  };

  useEffect(() => {
    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const chart = useMemo(() => {
    const s = data?.series ?? [];
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['SPI', 'SPEI'], textStyle: { color: '#64748b', fontSize: 11 } },
      grid: { left: 34, right: 12, top: 28, bottom: 20 },
      xAxis: { type: 'category', data: s.map((p) => p.month ?? ''), axisLabel: { fontSize: 9, color: '#94a3b8', interval: 11 } },
      yAxis: { type: 'value', axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(100,116,139,0.15)' } } },
      series: [
        { name: 'SPI', type: 'line', data: s.map((p) => p.spi), smooth: true, showSymbol: false, lineStyle: { color: '#0d9488', width: 2 }, areaStyle: { color: 'rgba(13,148,136,0.08)' } },
        { name: 'SPEI', type: 'line', data: s.map((p) => p.spei), smooth: true, showSymbol: false, lineStyle: { color: '#f59e0b', width: 1.5 }, areaStyle: { color: 'rgba(245,158,11,0.06)' } },
      ],
    };
  }, [data]);

  const level = data?.latest?.spi_class?.level ?? 'unknown';
  const color = LEVEL_COLOR[level] ?? '#94a3b8';

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <Droplets size={17} /> پایش خشکسالی (SPI / SPEI)
        </h3>
        {status === 'ok' && data?.latest && (
          <span style={{ fontSize: '0.72rem', fontWeight: 800, padding: '0.25rem 0.65rem', borderRadius: 999, background: `${color}1a`, color }}>
            ⚠ {data.latest.spi_class?.label ?? '—'} · SPI {data.latest.spi}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.6rem' }}>
        <input type="number" step="0.1" value={lat} onChange={(e) => setLat(parseFloat(e.target.value))} title="عرض جغرافیایی" style={{ width: 80, padding: '0.3rem 0.5rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.75rem' }} />
        <input type="number" step="0.1" value={lon} onChange={(e) => setLon(parseFloat(e.target.value))} title="طول جغرافیایی" style={{ width: 80, padding: '0.3rem 0.5rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.75rem' }} />
        <select value={months} onChange={(e) => setMonths(parseInt(e.target.value, 10))} style={{ padding: '0.3rem 0.5rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.75rem' }}>
          {[1, 3, 6, 12].map((m) => (
            <option key={m} value={m}>مقیاس {m} ماهه</option>
          ))}
        </select>
        <button onClick={() => void run()} disabled={status === 'loading'} style={{ padding: '0.35rem 0.8rem', borderRadius: 8, border: 'none', cursor: 'pointer', background: 'var(--color-primary)', color: '#fff', fontWeight: 700, fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
          <RefreshCw size={12} /> {status === 'loading' ? 'در حال محاسبه…' : 'محاسبه'}
        </button>
      </div>

      {status === 'loading' && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت داده واقعی ERA5…</p>}
      {status === 'error' && <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ {data?.error}</p>}

      {status === 'ok' && data && (
        <>
          <ReactECharts option={chart} style={{ height: 200, width: '100%' }} notMerge />
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.74rem', marginTop: '0.3rem' }}>
            <span style={{ padding: '0.3rem 0.6rem', borderRadius: 8, background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
              آخرین ماه: <strong>{data.latest?.month}</strong> · SPI {data.latest?.spi} / SPEI {data.latest?.spei}
            </span>
            <span style={{ padding: '0.3rem 0.6rem', borderRadius: 8, background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
              ماه‌های زیر -۱: <strong>{data.summary?.months_below_minus1}</strong>
            </span>
            <span style={{ padding: '0.3rem 0.6rem', borderRadius: 8, background: 'var(--color-bg)', border: '1px solid var(--color-border)' }}>
              بدترین SPI: <strong>{data.summary?.worst_spi}</strong>
            </span>
          </div>
          {data.alert && (
            <p style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <AlertTriangle size={11} /> هشدار اولیه: کانال داشبورد فعال؛ اتصال USSD/SMS پس از فراهم‌شدن درگاه پیامک انجام می‌شود.
            </p>
          )}
          {data.note && <p style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', margin: '0.3rem 0 0' }}>{data.note}</p>}
        </>
      )}
    </div>
  );
};
