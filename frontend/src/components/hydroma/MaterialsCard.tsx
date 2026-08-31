import React, { useState } from 'react';
import { Package, FlaskConical, Calculator } from 'lucide-react';

interface Material {
  name: string;
  mass_kg: number;
  carbon_content: number;
  nitrogen_content: number;
}

const PRESETS: Material[] = [
  { name: 'Straw', mass_kg: 200, carbon_content: 45, nitrogen_content: 0.5 },
  { name: 'Cow Manure', mass_kg: 300, carbon_content: 25, nitrogen_content: 1.5 },
  { name: 'Green Waste', mass_kg: 150, carbon_content: 30, nitrogen_content: 1.2 },
];

/**
 * فاز تکمیلی — انبارداری/مواد: محاسبه C/N کمپوست (اندپوینت واقعی بک‌اند).
 */
export const MaterialsCard: React.FC = () => {
  const [rows, setRows] = useState<Material[]>(PRESETS);
  const [result, setResult] = useState<{ cn_ratio?: number; status?: string } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const calc = async () => {
    setErr(null);
    try {
      const res = await fetch('/api/v1/materials/calculate-compost', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ materials: rows.filter((r) => r.mass_kg > 0) }),
      });
      const d = await res.json();
      if (res.ok) setResult(d);
      else setErr(String(d.detail ?? 'خطا'));
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'خطا');
    }
  };

  const ratio = result?.cn_ratio ?? 0;
  const ok = ratio >= 25 && ratio <= 35;

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
          <Package size={17} /> انبارداری و مواد — فرمول کمپوست (C/N)
        </h3>
        <span style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
          FAO: نسبت بهینه ۲۵–۳۵
        </span>
      </div>

      {rows.map((r, i) => (
        <div
          key={r.name}
          style={{
            display: 'grid',
            gridTemplateColumns: '1.2fr 1fr 1fr 1fr',
            gap: '0.3rem',
            marginBottom: '0.35rem',
            alignItems: 'center',
          }}
        >
          <span style={{ fontSize: '0.74rem', fontWeight: 700 }}>{r.name}</span>
          <input
            type="number"
            value={r.mass_kg}
            onChange={(e) =>
              setRows(
                rows.map((x, j) =>
                  j === i ? { ...x, mass_kg: parseFloat(e.target.value) || 0 } : x
                )
              )
            }
            title="mass kg"
            style={{
              padding: '0.25rem 0.4rem',
              borderRadius: 6,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
              fontSize: '0.7rem',
              width: '100%',
            }}
          />
          <span style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)' }}>
            C {r.carbon_content}٪
          </span>
          <span style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)' }}>
            N {r.nitrogen_content}٪
          </span>
        </div>
      ))}

      <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center', marginTop: '0.4rem' }}>
        <button
          onClick={() => void calc()}
          style={{
            padding: '0.35rem 0.85rem',
            borderRadius: 8,
            border: 'none',
            cursor: 'pointer',
            background: 'var(--color-primary)',
            color: '#fff',
            fontWeight: 700,
            fontSize: '0.75rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.3rem',
          }}
        >
          <Calculator size={12} /> محاسبه نسبت C/N
        </button>
        {result && (
          <span style={{ fontSize: '0.78rem', fontWeight: 800, color: ok ? '#0d9488' : '#b45309' }}>
            <FlaskConical size={12} style={{ verticalAlign: -2 }} /> C/N = {ratio} —{' '}
            {result?.status}
          </span>
        )}
        {err && <span style={{ fontSize: '0.74rem', color: '#ef4444' }}>⚠️ {err}</span>}
      </div>
      <p
        style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}
      >
        محاسبه واقعی با فرمول‌ساز کمپوست بک‌اند (مواد ورودی: کاه، کود دامی، بقایای سبز).
      </p>
    </div>
  );
};
