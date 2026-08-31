import React, { useEffect, useState } from 'react';
import { ShieldCheck, FileBadge, Download, Plus, Inbox } from 'lucide-react';

interface CreditRow {
  id?: string;
  project_id?: string;
  owner_id?: string;
  amount?: number;
  issued_at?: string;
  retired?: boolean;
}

interface QueueRow {
  id?: string;
  project_id?: string;
  module?: string;
  status?: string;
  standard?: string;
  algorithm?: string;
}

/**
 * فاز ۷ — ممیزی و اعتبار کربن: صف ممیزی، صدور اعتبار (فقط مدیر)، فهرست
 * اعتبارها و دانلود گواهی PDF فارسی. همه درخواست‌ها با JWT کاربر و
 * بررسی نقش در سمت سرور (RLS + توابع SECURITY DEFINER).
 */
export const AuditCard: React.FC = () => {
  const [token] = useState<string | null>(() => localStorage.getItem('eco_token'));
  const [role, setRole] = useState<string | null>(null);
  const [credits, setCredits] = useState<CreditRow[]>([]);
  const [queue, setQueue] = useState<QueueRow[]>([]);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [err, setErr] = useState<string | null>(null);
  const [form, setForm] = useState({ project_id: '', amount: '10' });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus('ok');
      return;
    }
    let alive = true;
    (async () => {
      try {
        const [pr, cr, qr] = await Promise.all([
          fetch(`/api/v1/supabase/profile?token=${encodeURIComponent(token)}`).then((r) =>
            r.json()
          ),
          fetch(`/api/v1/audit/credits?token=${encodeURIComponent(token)}`).then((r) => r.json()),
          fetch(`/api/v1/audit/queue?token=${encodeURIComponent(token)}&limit=10`).then((r) =>
            r.json()
          ),
        ]);
        if (!alive) return;
        if (pr.status === 'ok') setRole(pr.profile?.role ?? null);
        if (cr.status === 'ok') setCredits(cr.credits ?? []);
        if (qr.status === 'ok') setQueue(qr.queue ?? []);
        setStatus('ok');
      } catch {
        if (alive) setStatus('error');
      }
    })();
    return () => {
      alive = false;
    };
  }, [token]);

  const issue = async () => {
    if (!token || !form.project_id.trim()) return;
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const q = new URLSearchParams({
        token,
        project_id: form.project_id.trim(),
        amount: form.amount,
      });
      const res = await fetch(`/api/v1/audit/credits?${q.toString()}`, { method: 'POST' });
      const d = (await res.json()) as { status?: string; credit?: unknown[]; error?: string };
      if (d.status === 'ok') {
        setMsg('اعتبار صادر شد ✅');
        setForm({ ...form, project_id: '' });
        const cr = await fetch(`/api/v1/audit/credits?token=${encodeURIComponent(token)}`).then(
          (r) => r.json()
        );
        if (cr.status === 'ok') setCredits(cr.credits ?? []);
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
          <ShieldCheck size={17} /> ممیزی و اعتبار کربن
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          {role === 'admin' ? 'مدیر' : role === 'auditor' ? 'ممیزی' : 'کشاورز'} · {credits.length}{' '}
          اعتبار
        </span>
      </div>

      {!token && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          برای مشاهده اعتبارها و ممیزی وارد شوید.
        </p>
      )}
      {status === 'loading' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>
      )}
      {status === 'error' && (
        <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ خطا در دریافت داده‌ها</p>
      )}

      {token && status === 'ok' && (
        <>
          {/* صف ممیزی */}
          <div
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              margin: '0.2rem 0 0.4rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Inbox size={13} /> صف راستی‌آزمایی
          </div>
          {queue.length === 0 ? (
            <p
              style={{
                fontSize: '0.74rem',
                color: 'var(--color-text-secondary)',
                padding: '0.4rem 0',
              }}
            >
              صف خالی است — پس از ثبت پروژه و ارسال داده برای راستی‌آزمایی، موارد اینجا ظاهر
              می‌شوند.
            </p>
          ) : (
            queue.map((q) => (
              <div
                key={q.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: '0.5rem',
                  padding: '0.3rem 0.1rem',
                  borderBottom: '1px dashed var(--color-border)',
                  fontSize: '0.74rem',
                }}
              >
                <span>
                  {q.module ?? '—'} · {q.standard ?? '—'}
                </span>
                <span style={{ color: 'var(--color-text-secondary)' }}>{q.status}</span>
              </div>
            ))
          )}

          {/* صدور اعتبار — فقط مدیر */}
          {role === 'admin' && (
            <div
              style={{
                margin: '0.8rem 0',
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
                <Plus size={13} /> صدور اعتبار کربن (tCO2e)
              </div>
              <div
                style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}
              >
                <input
                  value={form.project_id}
                  onChange={(e) => setForm({ ...form, project_id: e.target.value })}
                  placeholder="شناسه پروژه"
                  style={{
                    padding: '0.35rem 0.5rem',
                    borderRadius: 8,
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-surface)',
                    color: 'var(--color-text)',
                    width: 210,
                  }}
                />
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                  title="مقدار tCO2e"
                  style={{
                    padding: '0.35rem 0.5rem',
                    borderRadius: 8,
                    border: '1px solid var(--color-border)',
                    background: 'var(--color-surface)',
                    color: 'var(--color-text)',
                    width: 90,
                  }}
                />
                <button
                  onClick={() => void issue()}
                  disabled={busy || !form.project_id.trim()}
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
                  {busy ? 'در حال صدور…' : 'صدور اعتبار'}
                </button>
              </div>
              {msg && (
                <p style={{ fontSize: '0.76rem', color: '#10b981', margin: '0.4rem 0 0' }}>
                  ✓ {msg}
                </p>
              )}
              {err && (
                <p style={{ fontSize: '0.76rem', color: '#ef4444', margin: '0.4rem 0 0' }}>
                  ⚠️ {err}
                </p>
              )}
            </div>
          )}

          {/* اعتبارهای من */}
          <div
            style={{
              fontSize: '0.78rem',
              fontWeight: 700,
              margin: '0.2rem 0 0.4rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <FileBadge size={13} /> اعتبارهای صادرشده
          </div>
          {credits.length === 0 ? (
            <p
              style={{
                fontSize: '0.74rem',
                color: 'var(--color-text-secondary)',
                padding: '0.4rem 0',
              }}
            >
              هنوز اعتباری صادر نشده است.
            </p>
          ) : (
            credits.map((c) => (
              <div
                key={c.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.35rem 0.1rem',
                  borderBottom: '1px dashed var(--color-border)',
                  fontSize: '0.76rem',
                }}
              >
                <span>
                  <strong>{c.amount}</strong> tCO2e · {String(c.issued_at ?? '').slice(0, 10)}
                  {c.retired ? ' · 🔒 بازنشسته' : ''}
                </span>
                <a
                  href={`/api/v1/audit/certificate/${c.project_id}?token=${encodeURIComponent(token)}`}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: '#0d9488',
                    textDecoration: 'none',
                  }}
                >
                  <Download size={13} /> گواهی PDF
                </a>
              </div>
            ))
          )}

          <p
            style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-secondary)',
              margin: '0.6rem 0 0',
            }}
          >
            صدور اعتبار فقط برای مدیر انجام می‌شود؛ رأی ممیزی مخصوص نقش auditor — همه بررسی‌ها در
            سمت سرور (RLS + توابع امن).
          </p>
        </>
      )}
    </div>
  );
};
