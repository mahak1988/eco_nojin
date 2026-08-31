import React, { useState } from 'react';
import { FlaskConical, Play, RefreshCw } from 'lucide-react';

interface LabCardProps {
  lat: number;
  lon: number;
}

interface LabPair {
  lab_id?: string;
  lat?: number;
  lon?: number;
  measured_soc_t_ha?: number;
  modelled_soc_t_ha?: number;
  error_t_ha?: number;
}

interface CompareResult {
  status?: string;
  n?: number;
  mean_measured_t_ha?: number;
  mean_modelled_t_ha?: number;
  bias_t_ha?: number;
  rmse_t_ha?: number;
  mape_pct?: number;
  r2?: number | null;
  kge?: number | null;
  note?: string;
  message?: string;
  pairs?: LabPair[];
}

const DEMO_ROWS = [
  { lat: 35.498, lon: 51.503, soc_t_ha: 58.2, lab: 'AgriLab', sampled_at: '2026-08-20' },
  { lat: 35.507, lon: 51.495, soc_t_ha: 61.4, lab: 'AgriLab' },
  { lat: 35.512, lon: 51.508, soc_t_ha: 63.9, lab: 'AgriLab' },
  { lat: 35.494, lon: 51.511, soc_t_ha: 65.2, lab: 'AgriLab' },
  { lat: 35.505, lon: 51.499, soc_t_ha: 67.1, lab: 'AgriLab' },
];

/**
 * فاز ۴-د — اتصال داده آزمایشگاهی واقعی و مقایسه با مدل SoilGrids.
 * آمار (bias/RMSE/MAPE/R2) فقط با داده واقعی کاربر محاسبه میشود؛ KGE صادقانه null است.
 */
export const LabCompareCard: React.FC<LabCardProps> = () => {
  const [rowsText, setRowsText] = useState(JSON.stringify(DEMO_ROWS, null, 2));
  const [stored, setStored] = useState<{
    status?: string;
    added?: number;
    total?: number;
    errors?: string[];
  } | null>(null);
  const [cmp, setCmp] = useState<CompareResult | null>(null);
  const [busy, setBusy] = useState<'store' | 'compare' | null>(null);

  const post = async (url: string, body?: unknown) => {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as Record<string, unknown>;
  };

  const store = async () => {
    setBusy('store');
    try {
      const rows = JSON.parse(rowsText) as unknown[];
      setStored((await post('/api/mrv/lab/samples', { samples: rows })) as never);
    } catch (err) {
      setStored({ errors: [err instanceof Error ? err.message : 'خطا'] });
    } finally {
      setBusy(null);
    }
  };

  const compare = async () => {
    setBusy('compare');
    try {
      setCmp((await post('/api/mrv/lab/compare')) as never);
    } catch (err) {
      setCmp({ message: err instanceof Error ? err.message : 'خطا' });
    } finally {
      setBusy(null);
    }
  };

  const stats: [string, string][] = cmp?.status
    ? [
        ['تعداد نمونه', `${cmp.n ?? '—'}`],
        ['میانگین اندازهگیری', `${cmp.mean_measured_t_ha ?? '—'} t C/ha`],
        ['میانگین مدل (SoilGrids)', `${cmp.mean_modelled_t_ha ?? '—'} t C/ha`],
        ['Bias', `${cmp.bias_t_ha ?? '—'} t C/ha`],
        ['RMSE', `${cmp.rmse_t_ha ?? '—'} t C/ha`],
        ['MAPE', `${cmp.mape_pct ?? '—'} %`],
        ['R²', `${cmp.r2 ?? '—'}`],
        ['KGE', cmp.kge == null ? 'نیاز به سری مشاهده' : `${cmp.kge}`],
      ]
    : [];

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '0.9rem',
        }}
      >
        <h3
          style={{
            fontSize: '1.05rem',
            fontWeight: 800,
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: '#0d9488',
          }}
        >
          <FlaskConical size={17} /> داده آزمایشگاهی و مقایسه با مدل (۴-د)
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          SoilGrids · honesty: KGE نیازمند سری مشاهدهای
        </span>
      </div>

      <textarea
        value={rowsText}
        onChange={(e) => setRowsText(e.target.value)}
        rows={7}
        spellCheck={false}
        style={{
          width: '100%',
          fontFamily: 'monospace',
          fontSize: '0.72rem',
          borderRadius: 10,
          border: '1px solid var(--color-border)',
          background: 'var(--color-bg)',
          color: 'var(--color-text)',
          padding: '0.6rem',
          boxSizing: 'border-box',
          direction: 'ltr',
          textAlign: 'left',
        }}
      />
      <p
        style={{
          fontSize: '0.7rem',
          color: 'var(--color-text-secondary)',
          margin: '0.3rem 0 0.7rem',
        }}
      >
        ⚠️ ردیفهای پیشفرض «demo» هستند — با نتایج آزمایشگاه واقعی (lat, lon, soc_t_ha) جایگزین کنید.
      </p>

      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
        <button
          onClick={() => void store()}
          disabled={busy !== null}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 10,
            border: 'none',
            cursor: 'pointer',
            background: 'var(--color-primary)',
            color: '#fff',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.82rem',
          }}
        >
          <Play size={13} /> {busy === 'store' ? 'در حال ثبت…' : 'ثبت نمونهها'}
        </button>
        <button
          onClick={() => void compare()}
          disabled={busy !== null}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 10,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            cursor: 'pointer',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.82rem',
            color: 'var(--color-text)',
          }}
        >
          <RefreshCw size={13} /> {busy === 'compare' ? 'در حال مقایسه…' : 'مقایسه با مدل'}
        </button>
      </div>

      {stored && (
        <p
          style={{
            fontSize: '0.8rem',
            margin: '0.7rem 0 0',
            color: stored.errors?.length ? '#ef4444' : '#10b981',
          }}
        >
          {stored.errors?.length
            ? `⚠️ ${stored.errors.join(' | ')}`
            : `✅ ${stored.added} نمونه ثبت شد (مجموع: ${stored.total})`}
        </p>
      )}

      {cmp?.message && (
        <p style={{ fontSize: '0.82rem', color: '#f59e0b', margin: '0.7rem 0 0' }}>
          ⚠️ {cmp.message}
        </p>
      )}

      {stats.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
            gap: '0.4rem',
            marginTop: '0.9rem',
          }}
        >
          {stats.map(([k, v]) => (
            <div
              key={k}
              style={{
                padding: '0.45rem 0.55rem',
                borderRadius: 9,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)' }}>{k}</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700 }}>{v}</div>
            </div>
          ))}
        </div>
      )}

      {cmp?.pairs && cmp.pairs.length > 0 && (
        <div style={{ marginTop: '0.8rem', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.74rem' }}>
            <thead>
              <tr style={{ color: 'var(--color-text-secondary)' }}>
                <th style={{ textAlign: 'right', padding: '0.35rem' }}>شناسه</th>
                <th style={{ textAlign: 'right', padding: '0.35rem' }}>مختصات</th>
                <th style={{ textAlign: 'right', padding: '0.35rem' }}>آزمایشگاه (t C/ha)</th>
                <th style={{ textAlign: 'right', padding: '0.35rem' }}>مدل (t C/ha)</th>
                <th style={{ textAlign: 'right', padding: '0.35rem' }}>خطا</th>
              </tr>
            </thead>
            <tbody>
              {cmp.pairs.map((p) => (
                <tr key={p.lab_id} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '0.35rem' }}>{p.lab_id}</td>
                  <td style={{ padding: '0.35rem' }}>
                    {p.lat}, {p.lon}
                  </td>
                  <td style={{ padding: '0.35rem' }}>{p.measured_soc_t_ha}</td>
                  <td style={{ padding: '0.35rem' }}>{p.modelled_soc_t_ha}</td>
                  <td
                    style={{
                      padding: '0.35rem',
                      color: (p.error_t_ha ?? 0) > 0 ? '#ef4444' : '#10b981',
                      fontWeight: 700,
                    }}
                  >
                    {(p.error_t_ha ?? 0) > 0 ? '+' : ''}
                    {p.error_t_ha}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!cmp && !stored && (
        <p
          style={{
            fontSize: '0.76rem',
            color: 'var(--color-text-secondary)',
            margin: '0.8rem 0 0',
          }}
        >
          اعتبارسنجی (KGE ≥ 0.55) تا فراهمشدن سری زمانی مشاهدهای صادقانه غیرفعال است (W-001).
        </p>
      )}
    </div>
  );
};
