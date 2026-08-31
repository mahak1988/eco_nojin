import React, { useEffect, useState } from 'react';
import { Boxes, Leaf, Truck } from 'lucide-react';

/**
 * فاز تکمیلی — دفتر کل بلاک‌چین: آمار ثبت کربن و زنجیره تأمین (واقعی، صادقانه).
 */
export const BlockchainCard: React.FC = () => {
  const [carbon, setCarbon] = useState<Record<string, unknown> | null>(null);
  const [supply, setSupply] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [c, s] = await Promise.all([
          fetch('/api/v1/blockchain/carbon/stats').then((r) => r.json()),
          fetch('/api/v1/blockchain/supply-chain/stats').then((r) => r.json()),
        ]);
        setCarbon(c);
        setSupply(s);
      } catch (ex) {
        setErr(ex instanceof Error ? ex.message : 'خطا');
      }
    })();
  }, []);

  const render = (obj: Record<string, unknown> | null) =>
    obj
      ? Object.entries(obj).map(([k, v]) => (
          <div
            key={k}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.72rem',
              padding: '0.12rem 0',
              borderBottom: '1px dashed var(--color-border)',
            }}
          >
            <span style={{ color: 'var(--color-text-secondary)' }}>{k}</span>
            <span style={{ fontWeight: 700 }}>{String(v)}</span>
          </div>
        ))
      : null;

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.7rem' }}>
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
          <Boxes size={17} /> دفتر کل بلاک‌چین (کربن + زنجیره تأمین)
        </h3>
      </div>

      {err && <p style={{ fontSize: '0.76rem', color: '#ef4444' }}>⚠️ {err}</p>}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.5rem',
        }}
      >
        <div
          style={{
            border: '1px solid var(--color-border)',
            borderRadius: 10,
            padding: '0.5rem 0.65rem',
            background: 'var(--color-bg)',
          }}
        >
          <div
            style={{
              fontSize: '0.7rem',
              fontWeight: 800,
              marginBottom: '0.3rem',
              color: '#0d9488',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            <Leaf size={11} /> ثبت کربن
          </div>
          {render(carbon)}
          {carbon && Object.keys(carbon).length === 0 && (
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              — بدون داده
            </div>
          )}
        </div>
        <div
          style={{
            border: '1px solid var(--color-border)',
            borderRadius: 10,
            padding: '0.5rem 0.65rem',
            background: 'var(--color-bg)',
          }}
        >
          <div
            style={{
              fontSize: '0.7rem',
              fontWeight: 800,
              marginBottom: '0.3rem',
              color: '#0d9488',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
            }}
          >
            <Truck size={11} /> زنجیره تأمین
          </div>
          {render(supply)}
          {supply && Object.keys(supply).length === 0 && (
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              — بدون داده
            </div>
          )}
        </div>
      </div>
      <p
        style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}
      >
        آمار واقعی بک‌اند؛ با ثبت پروژه‌ها و محصولات واقعی پر می‌شود.
      </p>
    </div>
  );
};
