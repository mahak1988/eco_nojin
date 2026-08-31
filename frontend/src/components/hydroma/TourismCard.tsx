import React, { useEffect, useState } from 'react';
import { Compass, MapPin } from 'lucide-react';

interface TourismStatus {
  status?: string;
  module?: string;
  capabilities?: string[];
  note?: string;
}

/**
 * فاز تکمیلی — گردشگری بوم‌گردی: وضعیت صادقانه ماژول بک‌اند.
 */
export const TourismCard: React.FC = () => {
  const [data, setData] = useState<TourismStatus | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/v1/tourism/status')
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setErr(e instanceof Error ? e.message : 'خطا'));
  }, []);

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
          <Compass size={17} /> گردشگری بوم‌گردی
        </h3>
        {data?.status && (
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 800,
              padding: '0.22rem 0.6rem',
              borderRadius: 999,
              background: data.status === 'requires_setup' ? '#fef3c7' : '#ecfdf5',
              color: data.status === 'requires_setup' ? '#b45309' : '#065f46',
            }}
          >
            {data.status === 'requires_setup' ? 'در انتظار راه‌اندازی دیتابیس' : data.status}
          </span>
        )}
      </div>

      {err && <p style={{ fontSize: '0.76rem', color: '#ef4444' }}>⚠️ {err}</p>}

      {data && (
        <>
          <ul
            style={{
              margin: 0,
              padding: '0 1rem',
              fontSize: '0.76rem',
              color: 'var(--color-text)',
              lineHeight: 1.9,
            }}
          >
            {(data.capabilities ?? []).map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
          {data.note && (
            <p
              style={{
                fontSize: '0.68rem',
                color: 'var(--color-text-secondary)',
                margin: '0.5rem 0 0',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.3rem',
              }}
            >
              <MapPin size={11} style={{ marginTop: 2, flexShrink: 0 }} /> {data.note}
            </p>
          )}
        </>
      )}
    </div>
  );
};
