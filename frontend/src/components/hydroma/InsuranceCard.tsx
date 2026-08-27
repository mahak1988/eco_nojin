import React, { useEffect, useState } from 'react';
import { Umbrella, TrendingDown } from 'lucide-react';

interface InsResult {
  farm_id?: string;
  season_mean_ndvi?: number;
  reference_ndvi?: number;
  deficit?: number;
  trigger_active?: boolean;
  payout_rate?: number;
  note?: string;
}

/**
 * فاز تکمیلی — بیمه شاخص‌محور NDVI (اندپوینت واقعی بک‌اند، بدون ادعای اکچوئری).
 */
export const InsuranceCard: React.FC = () => {
  const [farmId, setFarmId] = useState('farm-001');
  const [refNdvi, setRefNdvi] = useState(0.6);
  const [series, setSeries] = useState('0.55, 0.52, 0.48, 0.50, 0.45');
  const [caps, setCaps] = useState<{ pricing?: boolean; note?: string } | null>(null);
  const [res, setRes] = useState<InsResult | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/insurance/capabilities')
      .then((r) => r.json())
      .then(setCaps)
      .catch(() => setCaps({ pricing: false, note: 'سرویس در دسترس نیست' }));
  }, []);

  const run = async () => {
    setErr(null);
    try {
      const ndvi_values = series.split(/[,،\s]+/).map(Number).filter((n) => !Number.isNaN(n));
      const res = await fetch('/api/v1/insurance/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ farm_id: farmId, ndvi_values, reference_ndvi: refNdvi }),
      });
      const d = await res.json();
      if (res.ok) setRes(d);
      else setErr(String(d.detail ?? 'خطا'));
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'خطا');
    }
  };

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <Umbrella size={17} /> بیمه شاخص‌محور (NDVI)
        </h3>
        {caps && caps.pricing === false && <span style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)' }}>بدون قیمت‌گذاری اکچوئری — صادقانه</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.35rem', marginBottom: '0.4rem' }}>
        <input value={farmId} onChange={(e) => setFarmId(e.target.value)} placeholder="farm_id" style={{ padding: '0.32rem 0.5rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.74rem' }} />
        <input type="number" step="0.01" value={refNdvi} onChange={(e) => setRefNdvi(parseFloat(e.target.value))} placeholder="reference NDVI" style={{ padding: '0.32rem 0.5rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.74rem' }} />
      </div>
      <textarea value={series} onChange={(e) => setSeries(e.target.value)} rows={2} placeholder="سری NDVI فصل (با کاما)" style={{ width: '100%', padding: '0.32rem 0.5rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.74rem', resize: 'vertical' }} />

      <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center', marginTop: '0.4rem' }}>
        <button onClick={() => void run()} style={{ padding: '0.35rem 0.85rem', borderRadius: 8, border: 'none', cursor: 'pointer', background: 'var(--color-primary)', color: '#fff', fontWeight: 700, fontSize: '0.75rem' }}>ارزیابی شاخص</button>
        {err && <span style={{ fontSize: '0.72rem', color: '#ef4444' }}>⚠️ {err}</span>}
      </div>

      {res && (
        <div style={{ marginTop: '0.55rem', padding: '0.55rem 0.65rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)', fontSize: '0.76rem' }}>
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', fontWeight: 700 }}>
            <span>میانگین NDVI: {res.season_mean_ndvi}</span>
            <span>کمبود: {(res.deficit ?? 0).toFixed(3)}</span>
            <span style={{ color: res.trigger_active ? '#b45309' : '#0d9488' }}>{res.trigger_active ? '⚠️ فعال (غیرعادی)' : 'عادی'}</span>
            <span>نرخ پرداخت: {((res.payout_rate ?? 0) * 100).toFixed(0)}٪</span>
          </div>
          {res.note && <p style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', margin: '0.3rem 0 0' }}><TrendingDown size={10} style={{ verticalAlign: -2 }} /> {res.note}</p>}
        </div>
      )}
      {caps?.note && <p style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)', margin: '0.45rem 0 0' }}>{caps.note}</p>}
    </div>
  );
};
