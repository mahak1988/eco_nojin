import React, { useState } from 'react';
import { Globe2, Play } from 'lucide-react';

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
export const MrvCard: React.FC<MrvCardProps> = ({ lat, lon }) => {
  const [area, setArea] = useState(100);
  const [practice, setPractice] = useState('conservation_ag');
  const [methodology, setMethodology] = useState('vm0032');
  const [result, setResult] = useState<MrvPayload | null>(null);
  const [loading, setLoading] = useState(false);

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
          body: JSON.stringify({ lat, lon, crop: 'wheat', area_ha: area, practice, methodology, use_kobo: false }),
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

  const c = result?.carbon;
  const delta = typeof c?.delta_co2e_total === 'number' ? c.delta_co2e_total : null;
  const negative = delta != null && delta < 0;
  const mode = String(c?.data_mode ?? '—');
  const koboStatus = String((result?.kobo as Record<string, unknown> | undefined)?.status ?? 'skipped');

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
        <button onClick={() => void run()} disabled={loading} style={{ padding: '0.5rem 1.1rem', borderRadius: 10, border: 'none', cursor: 'pointer', background: 'var(--color-primary)', color: '#fff', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem' }}>
          <Play size={13} /> {loading ? 'در حال محاسبه…' : 'محاسبه'}
        </button>
      </div>

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
        </div>
      )}

      {!result && !loading && (
        <p style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', margin: 0 }}>
          برآورد بر پایه زنجیره واقعی RothC (ERA5 + SoilGrids)؛ برای «تأیید میدانی»، حساب رایگان KoboToolbox بسازید (راهنما در docs/fa/40) — گواهی استاندارد نیازمند ثبت در رجیستری رسمی است.
        </p>
      )}
    </div>
  );
};
