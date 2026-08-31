import React, { useState } from 'react';
import { Play, Wallet } from 'lucide-react';
import ReactECharts from 'echarts-for-react';

interface EconomyCardProps {
  lat: number;
  lon: number;
}

interface EcoOutput {
  intervention?: string;
  intervention_label?: string;
  data_mode?: string;
  npv_usd?: number;
  payback_year?: number | null;
  livelihood_index?: number;
  benefits_usd?: {
    crop_yr?: number;
    water_yr?: number;
    carbon_once?: number;
    carbon_delta_tco2e?: number;
  };
  costs_usd?: { setup_once?: number; maint_yr?: number };
  baseline?: { yield_ton_ha?: number; supply_mcm?: number; soc_initial_t_ha?: number };
  intervention_run?: { yield_ton_ha?: number; supply_mcm?: number; soc_final_t_ha?: number };
  assumptions?: { yield_mult?: number; water_eff?: number; note?: string };
  prices?: Record<string, number>;
  note?: string;
}

const INTERVENTIONS = [
  ['conservation_ag', 'کشاورزی حفاظتی'],
  ['agroforestry', 'آگروفارستری'],
  ['terrace', 'تراسبندی'],
  ['rotational_grazing', 'چرای تناوبی'],
  ['none', 'بدون مداخله'],
] as const;

/**
 * فاز ۵ — اقتصاد معیشت: تحلیل هزینه-فایده مداخلات احیا بر پایه زنجیره علمی واقعی
 * (AquaCrop/Pywr/RothC) + قیمتهای پارامتریک. همه ارقام برآورد مدلیاند و صادقانه
 * برچسب میخورند؛ درآمد کربن داوطلبانه است و گواهی رسمی نیست.
 */
export const EconomyCard: React.FC<EconomyCardProps> = ({ lat, lon }) => {
  const [intervention, setIntervention] = useState('conservation_ag');
  const [area, setArea] = useState(100);
  const [slope, setSlope] = useState(10);
  const [result, setResult] = useState<EcoOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/motors/economy/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat,
          lon,
          area_ha: area,
          intervention,
          slope_pct: slope,
          discount_rate: 0.1,
          horizon_years: 20,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const d = (await res.json()) as {
        status?: string;
        outputs?: EcoOutput;
        error?: string | null;
      };
      if (d.status === 'failed') throw new Error(d.error ?? 'خطای موتور');
      setResult(d.outputs ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا');
    } finally {
      setLoading(false);
    }
  };

  const npv = result?.npv_usd;
  const positive = npv != null && npv >= 0;
  const li = result?.livelihood_index ?? null;

  const chartOption = result
    ? {
        tooltip: { trigger: 'axis' },
        grid: { left: 40, right: 16, top: 24, bottom: 28 },
        xAxis: {
          type: 'category',
          data: ['سود محصول/سال', 'سود آب/سال', 'کربن (یکبار)', 'هزینه راهاندازی', 'نگهداری/سال'],
          axisLabel: { fontSize: 9 },
        },
        yAxis: { type: 'value', name: 'USD', nameTextStyle: { fontSize: 9 } },
        series: [
          {
            type: 'bar',
            data: [
              { value: result.benefits_usd?.crop_yr ?? 0, itemStyle: { color: '#10b981' } },
              { value: result.benefits_usd?.water_yr ?? 0, itemStyle: { color: '#0ea5e9' } },
              { value: result.benefits_usd?.carbon_once ?? 0, itemStyle: { color: '#84cc16' } },
              { value: -(result.costs_usd?.setup_once ?? 0), itemStyle: { color: '#ef4444' } },
              { value: -(result.costs_usd?.maint_yr ?? 0), itemStyle: { color: '#f97316' } },
            ],
            label: {
              show: true,
              position: 'top',
              fontSize: 8,
              formatter: (p: { value: number }) => `${Math.round(p.value).toLocaleString()}`,
            },
          },
        ],
      }
    : null;

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
          <Wallet size={17} /> اقتصاد معیشت — هزینه-فایده مداخله (فاز ۵)
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          NPV ۲۰ ساله · نرخ تنزیل ۱۰٪ · قیمتها پارامتری
        </span>
      </div>

      <div
        style={{
          display: 'flex',
          gap: '0.6rem',
          alignItems: 'flex-end',
          flexWrap: 'wrap',
          marginBottom: '0.8rem',
        }}
      >
        <label
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.2rem',
            fontSize: '0.72rem',
            color: 'var(--color-text-secondary)',
          }}
        >
          مداخله
          <select
            value={intervention}
            onChange={(e) => setIntervention(e.target.value)}
            style={{
              padding: '0.4rem 0.6rem',
              borderRadius: 9,
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg)',
              color: 'var(--color-text)',
            }}
          >
            {INTERVENTIONS.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.2rem',
            fontSize: '0.72rem',
            color: 'var(--color-text-secondary)',
          }}
        >
          مساحت (ha)
          <input
            type="number"
            min="1"
            value={area}
            onChange={(e) => setArea(Number(e.target.value))}
            style={{
              padding: '0.4rem 0.6rem',
              borderRadius: 9,
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg)',
              color: 'var(--color-text)',
              width: 84,
            }}
          />
        </label>
        <label
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.2rem',
            fontSize: '0.72rem',
            color: 'var(--color-text-secondary)',
          }}
        >
          شیب (%)
          <input
            type="number"
            min="1"
            max="60"
            value={slope}
            onChange={(e) => setSlope(Number(e.target.value))}
            style={{
              padding: '0.4rem 0.6rem',
              borderRadius: 9,
              border: '1px solid var(--color-border)',
              background: 'var(--color-bg)',
              color: 'var(--color-text)',
              width: 72,
            }}
          />
        </label>
        <button
          onClick={() => void run()}
          disabled={loading}
          style={{
            padding: '0.5rem 1.1rem',
            borderRadius: 10,
            border: 'none',
            cursor: 'pointer',
            background: 'var(--color-primary)',
            color: '#fff',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.85rem',
          }}
        >
          <Play size={13} /> {loading ? 'در حال اجرای زنجیره (۲ بار)…' : 'محاسبه NPV'}
        </button>
      </div>

      {error && (
        <p style={{ color: '#ef4444', fontSize: '0.85rem', margin: '0 0 0.5rem' }}>⚠️ {error}</p>
      )}

      {result && (
        <>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1.4rem',
              flexWrap: 'wrap',
              marginBottom: '0.8rem',
            }}
          >
            <div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
                NPV (۲۰ ساله)
              </div>
              <div
                style={{
                  fontSize: '1.6rem',
                  fontWeight: 800,
                  color: positive ? '#10b981' : '#ef4444',
                }}
              >
                {npv != null
                  ? `${npv >= 0 ? '+' : ''}${npv.toLocaleString(undefined, { maximumFractionDigits: 0 })} $`
                  : '—'}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
                بازگشت سرمایه:{' '}
                {result.payback_year ? `سال ${result.payback_year}` : 'در افق ۲۰ ساله بازنگشت'} ·{' '}
                {result.intervention_label}
              </div>
            </div>
            <div style={{ minWidth: 220, flex: 1 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '0.72rem',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '0.25rem',
                }}
              >
                <span>شاخص معیشت</span>
                <span style={{ fontWeight: 800, color: '#0d9488' }}>{li ?? '—'} / 100</span>
              </div>
              <div
                style={{
                  height: 10,
                  borderRadius: 8,
                  background: 'var(--color-border)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${li ?? 0}%`,
                    height: '100%',
                    borderRadius: 8,
                    background: 'linear-gradient(90deg, #0d9488, #10b981)',
                  }}
                />
              </div>
              <div
                style={{
                  fontSize: '0.66rem',
                  color: 'var(--color-text-secondary)',
                  marginTop: '0.3rem',
                }}
              >
                ۳۵٪ عملکرد · ۳۰٪ آب · ۱۵٪ کربن · ۲۰٪ خاک — برآورد مدلی
              </div>
            </div>
          </div>

          {chartOption && <ReactECharts option={chartOption} style={{ height: 210 }} />}

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
              gap: '0.4rem',
              marginTop: '0.6rem',
            }}
          >
            {[
              [
                'عملکرد گندم',
                `${result.baseline?.yield_ton_ha ?? '—'} → ${result.intervention_run?.yield_ton_ha ?? '—'} t/ha`,
              ],
              [
                'تأمین آب',
                `${result.baseline?.supply_mcm ?? '—'} → ${result.intervention_run?.supply_mcm ?? '—'} MCM`,
              ],
              [
                'SOC',
                `${result.baseline?.soc_initial_t_ha ?? '—'} → ${result.intervention_run?.soc_final_t_ha ?? '—'} t C/ha`,
              ],
              ['ضریب فرضی عملکرد', `×${result.assumptions?.yield_mult ?? 1}`],
              ['ضریب فرضی آب', `×${result.assumptions?.water_eff ?? 1}`],
            ].map(([k, v]) => (
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
                <div style={{ fontSize: '0.8rem', fontWeight: 700 }}>{v}</div>
              </div>
            ))}
          </div>

          <p
            style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-secondary)',
              margin: '0.7rem 0 0',
              lineHeight: 1.7,
            }}
          >
            ⚠️ {result.note} قیمتها: گندم ${result.prices?.wheat_usd_t}/t · آب $
            {result.prices?.water_usd_m3}/m³ · کربن داوطلبانه ${result.prices?.carbon_usd_tco2e}
            /tCO2e.
          </p>
        </>
      )}

      {!result && !loading && !error && (
        <p style={{ fontSize: '0.76rem', color: 'var(--color-text-secondary)', margin: 0 }}>
          دو اجرای واقعی زنجیره (baseline و مداخله) با موتورهای AquaCrop/Pywr/RothC؛ ابزار تصمیمگیری
          است، نه توصیه سرمایهگذاری و نه گواهی کربن.
        </p>
      )}
    </div>
  );
};
