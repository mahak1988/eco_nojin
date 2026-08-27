import React, { useEffect, useState } from 'react';
import { Store, ExternalLink, BadgeCheck } from 'lucide-react';

interface StandardRow {
  id?: string;
  name?: string;
  organization?: string;
  description?: string | null;
  link?: string | null;
  category?: string | null;
}

interface MarketplaceData {
  status?: string;
  standards?: StandardRow[];
  projects_count?: number;
  error?: string;
}

const CATEGORY_LABEL: Record<string, string> = {
  carbon: 'کربن',
  laboratory: 'آزمایشگاه',
  satellite: 'ماهواره',
  water: 'آب',
  soil: 'خاک',
};

/**
 * فاز ۶-ب — کاتالوگ بازارچه روی همان دیتابیس Supabase: استانداردهای واقعی
 * (IPCC 2019، ISO 17025، NASA EOSDIS و…) + شمارنده پروژهها.
 */
export const MarketplaceCard: React.FC = () => {
  const [data, setData] = useState<MarketplaceData | null>(null);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch('/api/v1/supabase/marketplace');
        const d = (await res.json()) as MarketplaceData;
        if (!alive) return;
        if (d.status === 'ok') {
          setData(d);
          setStatus('ok');
        } else {
          setStatus('error');
          setData({ status: 'error', error: String(d.error ?? 'خطا') });
        }
      } catch (err) {
        if (!alive) return;
        setStatus('error');
        setData({ status: 'error', error: err instanceof Error ? err.message : 'خطا' });
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <Store size={17} /> بازارچه — کاتالوگ استانداردها
        </h3>
        {status === 'ok' && data && (
          <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
            {data.standards?.length ?? 0} استاندارد فعال · {data.projects_count ?? 0} پروژه
          </span>
        )}
      </div>

      {status === 'loading' && <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>}
      {status === 'error' && <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ {data?.error}</p>}

      {status === 'ok' && data?.standards && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: '0.5rem' }}>
          {data.standards.map((s) => (
            <div key={s.id} style={{ padding: '0.6rem 0.7rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontWeight: 700, fontSize: '0.82rem' }}>
                <BadgeCheck size={13} color="#0d9488" /> {s.name}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>{s.organization}</div>
              {s.description && <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>{s.description}</div>}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem' }}>
                <span style={{ fontSize: '0.66rem', padding: '0.15rem 0.45rem', borderRadius: 6, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
                  {CATEGORY_LABEL[s.category ?? ''] ?? s.category}
                </span>
                {s.link && (
                  <a href={s.link} target="_blank" rel="noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.7rem', color: 'var(--color-primary)', fontWeight: 600 }}>
                    <ExternalLink size={11} /> منبع
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {status === 'ok' && (
        <p style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', margin: '0.6rem 0 0' }}>
          داده واقعی از جدول standards (Supabase) — بازارچه/LMS روی همین دیتابیس ساخته میشود.
        </p>
      )}
    </div>
  );
};
