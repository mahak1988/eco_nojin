import React, { useMemo, useState } from 'react';
import { Zap, Mountain, Leaf, Info } from 'lucide-react';

/**
 * فاز ۸-ب — شبیه‌ساز سبک مرورگر (what-if فوری):
 * RUSLE (فرسایش خاک) + RothC-لایت (کربن آلی خاک) با لغزنده‌ها — پاسخ < ۵۰۰ms.
 * نسخه سبک برای تعامل سریع؛ اجرای دقیق همان سناریو در بک‌اند انجام می‌شود.
 */
export const LightSimCard: React.FC = () => {
  const [rusle, setRusle] = useState({ r: 120, k: 0.032, ls: 1.4, c: 0.25, p: 0.8 });
  const [roth, setRoth] = useState({ input: 3.0, rate: 0.06, soc0: 40 });

  const soilLoss = useMemo(() => {
    const a = rusle.r * rusle.k * rusle.ls * rusle.c * rusle.p;
    return Math.round(a * 100) / 100;
  }, [rusle]);

  const socSeries = useMemo(() => {
    const out: number[] = [];
    let soc = roth.soc0;
    for (let y = 0; y <= 20; y++) {
      out.push(Math.round(soc * 10) / 10);
      soc = soc + roth.input - soc * roth.rate;
    }
    return out;
  }, [roth]);

  const lossClass =
    soilLoss < 5 ? 'کم' : soilLoss < 12 ? 'متوسط' : soilLoss < 25 ? 'زیاد' : 'بحرانی';
  const socDelta = Math.round((socSeries[20] - roth.soc0) * 10) / 10;

  const slider = (
    label: string,
    val: number,
    min: number,
    max: number,
    step: number,
    unit: string,
    set: (v: number) => void
  ) => (
    <label
      style={{
        fontSize: '0.72rem',
        color: 'var(--color-text-secondary)',
        display: 'block',
        marginBottom: '0.4rem',
      }}
    >
      {label}:{' '}
      <strong style={{ color: 'var(--color-text)' }}>
        {val}
        {unit}
      </strong>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={val}
        onChange={(e) => set(parseFloat(e.target.value))}
        style={{ display: 'block', width: '100%', accentColor: '#0d9488' }}
      />
    </label>
  );

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '0.7rem',
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
          <Zap size={17} /> شبیه‌ساز سبک مرورگر (what-if فوری)
        </h3>
        <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
          &lt; ۵۰۰ms · بدون درخواست به سرور
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '0.8rem',
        }}
      >
        {/* RUSLE */}
        <div
          style={{
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            padding: '0.7rem 0.8rem',
            background: 'var(--color-bg)',
          }}
        >
          <div
            style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              marginBottom: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Mountain size={13} /> RUSLE — فرسایش خاک (t/ha/yr)
          </div>
          {slider('باران‌فرسایندگی R', rusle.r, 50, 400, 5, ' MJ·mm/ha·h', (v) =>
            setRusle({ ...rusle, r: v })
          )}
          {slider('فرسایش‌پذیری خاک K', rusle.k, 0.005, 0.07, 0.001, '', (v) =>
            setRusle({ ...rusle, k: v })
          )}
          {slider('شیب/طول LS', rusle.ls, 0.2, 4, 0.1, '', (v) => setRusle({ ...rusle, ls: v }))}
          {slider('پوشش C', rusle.c, 0.001, 1, 0.01, '', (v) => setRusle({ ...rusle, c: v }))}
          {slider('عملیات حفاظتی P', rusle.p, 0.05, 1, 0.05, '', (v) =>
            setRusle({ ...rusle, p: v })
          )}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '0.3rem',
              padding: '0.45rem 0.6rem',
              borderRadius: 8,
              background: soilLoss >= 12 ? '#fef3c7' : '#ecfdf5',
            }}
          >
            <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>A = {soilLoss} t/ha/yr</span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 800,
                color: soilLoss >= 25 ? '#b91c1c' : soilLoss >= 12 ? '#b45309' : '#065f46',
              }}
            >
              {lossClass}
            </span>
          </div>
        </div>

        {/* RothC-lite */}
        <div
          style={{
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            padding: '0.7rem 0.8rem',
            background: 'var(--color-bg)',
          }}
        >
          <div
            style={{
              fontSize: '0.8rem',
              fontWeight: 800,
              marginBottom: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Leaf size={13} /> RothC-لایت — کربن آلی خاک (۲۰ سال)
          </div>
          {slider('ورودی کربن سالانه', roth.input, 0.5, 10, 0.1, ' t/ha/yr', (v) =>
            setRoth({ ...roth, input: v })
          )}
          {slider('نرخ تجزیه (k)', roth.rate, 0.01, 0.2, 0.005, ' 1/yr', (v) =>
            setRoth({ ...roth, rate: v })
          )}
          {slider('SOC اولیه', roth.soc0, 10, 100, 1, ' t/ha', (v) =>
            setRoth({ ...roth, soc0: v })
          )}
          <div
            style={{
              marginTop: '0.3rem',
              display: 'flex',
              gap: '0.2rem',
              alignItems: 'flex-end',
              height: 56,
              padding: '0.3rem 0.2rem 0',
              borderBottom: '1px solid var(--color-border)',
            }}
          >
            {socSeries.map((v, i) => (
              <div
                key={i}
                title={`سال ${i}: ${v} t/ha`}
                style={{
                  flex: 1,
                  background: i % 5 === 0 ? '#0d9488' : '#99f6e4',
                  borderRadius: '2px 2px 0 0',
                  height: `${Math.min(100, (v / roth.soc0) * 100)}%`,
                  minHeight: 3,
                }}
              />
            ))}
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: '0.3rem',
              fontSize: '0.72rem',
              color: 'var(--color-text-secondary)',
            }}
          >
            <span>سال ۰: {roth.soc0} t/ha</span>
            <span style={{ fontWeight: 800, color: socDelta >= 0 ? '#0d9488' : '#b45309' }}>
              Δ۲۰ سال: {socDelta >= 0 ? '+' : ''}
              {socDelta} t/ha
            </span>
          </div>
        </div>
      </div>

      <p
        style={{
          fontSize: '0.7rem',
          color: 'var(--color-text-secondary)',
          margin: '0.6rem 0 0',
          display: 'flex',
          alignItems: 'center',
          gap: '0.3rem',
        }}
      >
        <Info size={11} /> نسخه سبک برای پاسخ فوری به لغزنده‌ها — اجرای دقیق همان سناریو (زنجیره
        کامل علمی: RothC-26.3 / RUSLE + ERA5 + SoilGrids) در بک‌اند انجام می‌شود.
      </p>
    </div>
  );
};
