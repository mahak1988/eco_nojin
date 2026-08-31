import React, { useCallback, useEffect, useState } from 'react';
import { Store, ExternalLink, BadgeCheck, Plus, FolderKanban } from 'lucide-react';

interface StandardRow {
  id?: string;
  name?: string;
  organization?: string;
  description?: string | null;
  link?: string | null;
  category?: string | null;
}

interface ProjectRow {
  id?: string;
  name?: string;
  project_type?: string;
  area_ha?: number;
  duration_years?: number;
  status?: string;
  created_at?: string;
}

interface MarketplaceData {
  status?: string;
  standards?: StandardRow[];
  projects?: ProjectRow[];
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

const TYPE_LABEL: Record<string, string> = {
  soil_carbon: 'کربن خاک',
  agroforestry: 'آگروفارستری',
  biochar: 'بیوچار',
};

/**
 * فاز ۶-ب/ج — بازارچه روی همان دیتابیس Supabase: کاتالوگ استانداردهای واقعی +
 * ایجاد واقعی پروژه کربن با مالکیت auth.uid() (RLS-ready).
 */
export const MarketplaceCard: React.FC = () => {
  const [data, setData] = useState<MarketplaceData | null>(null);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [token] = useState<string | null>(() => localStorage.getItem('eco_token'));
  const [role, setRole] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', type: 'soil_carbon', area: '100', years: '20' });
  const [own, setOwn] = useState<ProjectRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/supabase/marketplace');
      const d = (await res.json()) as MarketplaceData;
      if (d.status === 'ok') {
        setData(d);
        setStatus('ok');
      } else {
        setStatus('error');
        setData({ status: 'error', error: String(d.error ?? 'خطا') });
      }
    } catch (e) {
      setStatus('error');
      setData({ status: 'error', error: e instanceof Error ? e.message : 'خطا' });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const loadOwn = useCallback(async (t: string) => {
    try {
      const res = await fetch(`/api/v1/supabase/carbon-projects?token=${encodeURIComponent(t)}`);
      const d = (await res.json()) as { status?: string; projects?: ProjectRow[]; error?: string };
      if (d.status === 'ok') setOwn(d.projects ?? []);
    } catch {
      /* ignore — shown via create errors */
    }
  }, []);

  useEffect(() => {
    if (token) void loadOwn(token);
  }, [token, loadOwn]);

  useEffect(() => {
    if (!token) return;
    let alive = true;
    (async () => {
      try {
        const res = await fetch(`/api/v1/supabase/profile?token=${encodeURIComponent(token)}`);
        const d = (await res.json()) as { status?: string; profile?: { role?: string } | null };
        if (alive && d.status === 'ok') setRole(d.profile?.role ?? null);
      } catch {
        /* keep unknown */
      }
    })();
    return () => {
      alive = false;
    };
  }, [token]);

  const createProject = async () => {
    if (!token) {
      setErr('برای ساخت پروژه ابتدا وارد شوید (ورود واقعی Supabase).');
      return;
    }
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const q = new URLSearchParams({
        token,
        name: form.name,
        project_type: form.type,
        area_ha: form.area,
        duration_years: form.years,
      });
      const res = await fetch(`/api/v1/supabase/carbon-projects?${q.toString()}`, {
        method: 'POST',
      });
      const d = (await res.json()) as { status?: string; project?: ProjectRow; error?: string };
      if (d.status === 'ok') {
        setMsg(`پروژه «${d.project?.name}» با مالکیت شما ساخته شد (${d.project?.status}).`);
        setForm({ ...form, name: '' });
        void loadOwn(token);
      } else {
        setErr(String(d.error ?? 'خطا'));
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'خطا');
    } finally {
      setBusy(false);
    }
  };

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
          <Store size={17} /> بازارچه — پروژه‌ها و استانداردها
        </h3>
        {status === 'ok' && data && (
          <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
            {data.standards?.length ?? 0} استاندارد · {data.projects_count ?? 0} پروژه
          </span>
        )}
        {role && (
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 800,
              padding: '0.2rem 0.55rem',
              borderRadius: 999,
              background: role === 'admin' ? '#fef3c7' : '#ecfdf5',
              color: role === 'admin' ? '#92400e' : '#065f46',
              border: '1px solid var(--color-border)',
            }}
          >
            نقش: {role === 'admin' ? 'مدیر' : role === 'auditor' ? 'ممیزی' : 'کشاورز'}
          </span>
        )}
      </div>

      {status === 'loading' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>
      )}
      {status === 'error' && (
        <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ {data?.error}</p>
      )}

      {/* ساخت پروژه کربن */}
      <div
        style={{
          marginBottom: '0.9rem',
          padding: '0.7rem 0.8rem',
          borderRadius: 10,
          border: '1px solid var(--color-border)',
          background: 'var(--color-bg)',
        }}
      >
        <div
          style={{
            fontSize: '0.78rem',
            fontWeight: 700,
            marginBottom: '0.4rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
          }}
        >
          <Plus size={13} /> ایجاد پروژه کربن (مالکیت شما — auth.uid)
        </div>
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="نام پروژه"
            style={{
              padding: '0.35rem 0.5rem',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
              width: 170,
            }}
          />
          <select
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value })}
            style={{
              padding: '0.35rem 0.5rem',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
            }}
          >
            {Object.entries(TYPE_LABEL).map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
          <input
            type="number"
            min="1"
            value={form.area}
            onChange={(e) => setForm({ ...form, area: e.target.value })}
            title="مساحت (ha)"
            style={{
              padding: '0.35rem 0.5rem',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
              width: 74,
            }}
          />
          <input
            type="number"
            min="1"
            max="50"
            value={form.years}
            onChange={(e) => setForm({ ...form, years: e.target.value })}
            title="مدت (سال)"
            style={{
              padding: '0.35rem 0.5rem',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'var(--color-surface)',
              color: 'var(--color-text)',
              width: 74,
            }}
          />
          <button
            onClick={() => void createProject()}
            disabled={busy || !form.name.trim()}
            style={{
              padding: '0.4rem 0.9rem',
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              background: 'var(--color-primary)',
              color: '#fff',
              fontWeight: 700,
              fontSize: '0.78rem',
            }}
          >
            {busy ? 'در حال ساخت…' : 'ساخت پروژه'}
          </button>
        </div>
        {msg && (
          <p style={{ fontSize: '0.76rem', color: '#10b981', margin: '0.4rem 0 0' }}>✅ {msg}</p>
        )}
        {err && (
          <p style={{ fontSize: '0.76rem', color: '#ef4444', margin: '0.4rem 0 0' }}>⚠️ {err}</p>
        )}
        {!token && (
          <p
            style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-secondary)',
              margin: '0.4rem 0 0',
            }}
          >
            وارد نشده‌اید — پس از ورود واقعی، مالکیت پروژه با auth.uid ثبت می‌شود.
          </p>
        )}
      </div>

      {/* پروژه‌های من */}
      {own.length > 0 && (
        <div style={{ marginBottom: '0.9rem' }}>
          <div
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              marginBottom: '0.35rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <FolderKanban size={13} /> پروژه‌های من ({own.length})
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '0.4rem',
            }}
          >
            {own.map((p) => (
              <div
                key={p.id}
                style={{
                  padding: '0.5rem 0.6rem',
                  borderRadius: 9,
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)',
                }}
              >
                <div style={{ fontSize: '0.8rem', fontWeight: 700 }}>{p.name}</div>
                <div style={{ fontSize: '0.68rem', color: 'var(--color-text-secondary)' }}>
                  {TYPE_LABEL[p.project_type ?? ''] ?? p.project_type} · {p.area_ha} ha ·{' '}
                  {p.duration_years} سال · {p.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {status === 'ok' && data?.standards && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))',
            gap: '0.5rem',
          }}
        >
          {data.standards.map((s) => (
            <div
              key={s.id}
              style={{
                padding: '0.6rem 0.7rem',
                borderRadius: 10,
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.25rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontWeight: 700,
                  fontSize: '0.82rem',
                }}
              >
                <BadgeCheck size={13} color="#0d9488" /> {s.name}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
                {s.organization}
              </div>
              {s.description && (
                <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
                  {s.description}
                </div>
              )}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '0.2rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.66rem',
                    padding: '0.15rem 0.45rem',
                    borderRadius: 6,
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-secondary)',
                  }}
                >
                  {CATEGORY_LABEL[s.category ?? ''] ?? s.category}
                </span>
                {s.link && (
                  <a
                    href={s.link}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      fontSize: '0.7rem',
                      color: 'var(--color-primary)',
                      fontWeight: 600,
                    }}
                  >
                    <ExternalLink size={11} /> منبع
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {status === 'ok' && (
        <p
          style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)', margin: '0.6rem 0 0' }}
        >
          داده واقعی از دیتابیس Supabase — پس از اجرای migration 0001، RLS مالکیت را الزامی می‌کند.
        </p>
      )}
    </div>
  );
};
