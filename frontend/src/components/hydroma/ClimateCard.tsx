import React, { useEffect, useMemo, useState } from 'react';
import { ThermometerSun, CloudRain, TrendingUp } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

interface ClimateData {
  status?: string;
  scenario?: string;
  baseline?: { tmean_c?: { mean?: number }; precip_mm_month?: { mean?: number }; dry_months_pct?: number };
  future?: { tmean_c?: { mean?: number }; precip_mm_month?: { mean?: number }; dry_months_pct?: number };
  delta?: { tmean_c?: number; precip_change_pct?: number | null; dry_months_pct_point_change?: number };
  risk_30y?: { heat_risk?: string; drought_risk?: string; note?: string };
  periods?: { baseline?: { start?: string; end?: string }; future?: { start?: string; end?: string } };
  note?: string;
  error?: string;
}

const SCENARIOS = [
  ['SSP126', 'پایدار (1.9W/m²)'],
  ['SSP245', 'میانه (4.5W/m²)'],
  ['SSP370', 'بالا (7.0W/m²)'],
  ['SSP585', 'فسیلی (8.5W/m²)'],
];

const RISK_BADGE: Record<string, { label: string; color: string }> = {
  low: { label: 'کم', color: '#10b981' },
  moderate: { label: 'متوسط', color: '#f59e0b' },
  high: { label: 'زیاد', color: '#ef4444' },
};

/**
 * فاز ۸-ب — سناریوهای اقلیمی CMIP6 (SSP) با داده واقعی رایگان:
 * مقایسه دهه ۲۰۴۰ با دهه ۲۰۱۰ (ERA5) + ریسک ۳۰ ساله.
 */
export const ClimateCard: React.FC = () => {
  const [scenario, setScenario] = useState('SSP245');
  const [data, setData] = useState<ClimateData | null>(null);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');

  const run = async (sc: string) => {
    setStatus('loading');
    try {
      const res = await fetch('/api/v1/motors/climate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: 35.7, lon: 51.4, scenario: sc }),
      });
      const d = (await res.json()) as ClimateData;
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
    void run(scenario);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const change = (sc: string) => {
    setScenario(sc);
    void run(sc);
  };

  const bar = useMemo(() => {
    if (!data) return null;
    const b = data.baseline;
    const f = data.future;
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['دهه ۲۰۱۰ (ERA5)', 'دهه ۲۰۴۰ (CMIP6)'], textStyle: { color: '#64748b', fontSize: 11 } },
      grid: { left: 40, right: 12, top: 28, bottom: 24 },
      xAxis: { type: 'category', data: ['دما میانگین (°C)', 'بارش ماهانه (mm)'], axisLabel: { fontSize: 10, color: '#94a3b8' } },
      yAxis: { type: 'value', axisLabel: { fontSize: 9, color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(100,116,139,0.15)' } } },
      series: [
        { name: 'دهه ۲۰۱۰ (ERA5)', type: 'bar', data: [b?.tmean_c?.mean ?? 0, b?.precip_mm_month?.mean ?? 0], itemStyle: { color: '#94a3b8' }, barWidth: 22 },
        { name: 'دهه ۲۰۴۰ (CMIP6)', type: 'bar', data: [f?.tmean_c?.mean ?? 0, f?.precip_mm_month?.mean ?? 0], itemStyle: { color: '#0d9488' }, barWidth: 22 },
      ],
    };
  }, [data]);

  const heat = data?.risk_30y?.heat_risk ?? 'low';
  const drought = data?.risk_30y?.drought_risk ?? 'low';

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <ThermometerSun size={17} /> سناریوهای اقلیمی CMIP6 (SSP)
        </h3>
        {status === 'ok' && <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>تهران · داده واقعی رایگان</span>}
      </div>

      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.6rem' }}>
        {SCENARIOS.map(([key, label]) => (
          <button
            key={key}
            title={label}
            onClick={() => change(key)}
            disabled={status === 'loading'}
            style={{ padding: '0.32rem 0.7rem', borderRadius: 8, border: '1px solid var(--color-border)', background: scenario === key ? 'var(--color-primary)' : 'var(--color-surface)', color: scenario === key ? '#fff' : 'var(--color-text)', cursor: 'pointer', fontSize: '0.72rem', fontWeight: 700 }}
          >
            {key}
          </button>
        ))}
      </div>

      {status === 'loading' && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت داده مدل اقلیمی…</p>}
      {status === 'error' && <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ {data?.error}</p>}

      {status === 'ok' && data && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.45rem', marginBottom: '0.5rem' }}>
            <div style={{ padding: '0.5rem 0.6rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
              <div style={{ fontSize: '0.64rem', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><TrendingUp size={10} /> Δ دما</div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: (data.delta?.tmean_c ?? 0) >= 0 ? '#b45309' : '#0d9488' }}>{data.delta?.tmean_c ?? 0} °C</div>
            </div>
            <div style={{ padding: '0.5rem 0.6rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
              <div style={{ fontSize: '0.64rem', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><CloudRain size={10} /> Δ بارش</div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: (data.delta?.precip_change_pct ?? 0) >= 0 ? '#0d9488' : '#b45309' }}>{data.delta?.precip_change_pct ?? 0}%</div>
            </div>
            <div style={{ padding: '0.5rem 0.6rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
              <div style={{ fontSize: '0.64rem', color: 'var(--color-text-secondary)' }}>ریسک گرما</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: RISK_BADGE[heat]?.color ?? '#64748b' }}>{RISK_BADGE[heat]?.label ?? heat}</div>
            </div>
            <div style={{ padding: '0.5rem 0.6rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
              <div style={{ fontSize: '0.64rem', color: 'var(--color-text-secondary)' }}>ریسک خشکسالی</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: RISK_BADGE[drought]?.color ?? '#64748b' }}>{RISK_BADGE[drought]?.label ?? drought}</div>
            </div>
          </div>
          {bar && <ReactECharts option={bar} style={{ height: 170, width: '100%' }} notMerge />}
          <p style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', margin: '0.4rem 0 0' }}>
            {data.note} · ماه‌های خشک: {data.baseline?.dry_months_pct}٪ ← {data.future?.dry_months_pct}٪ ({(data.delta?.dry_months_pct_point_change ?? 0) >= 0 ? '+' : ''}{data.delta?.dry_months_pct_point_change} واحد درصد)
          </p>
        </>
      )}
    </div>
  );
};
