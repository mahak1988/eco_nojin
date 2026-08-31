import React, { useEffect, useState } from 'react';
import { UserCircle2, Save, Wallet, BadgeCheck } from 'lucide-react';

interface ProfileRow {
  id?: string;
  display_name?: string | null;
  phone?: string | null;
  bio?: string | null;
  role?: string;
  language?: string;
  kyc_level?: number;
  wallet_address?: string | null;
}

interface WalletRow {
  eco_balance?: number;
  cct_balance?: number;
  level?: string;
  rank?: number;
}

/**
 * فاز ۸-الف — پروفایل کاربر با داده واقعی Supabase: نمایش و ویرایش
 * (display_name/phone/bio از platform_profiles، موجودی اکو/سی‌سی‌تی از users)
 * — همه با JWT کاربر و RLS مالکیت.
 */
export const ProfileCard: React.FC = () => {
  const [token] = useState<string | null>(() => localStorage.getItem('eco_token'));
  const [profile, setProfile] = useState<ProfileRow | null>(null);
  const [wallet, setWallet] = useState<WalletRow | null>(null);
  const [email, setEmail] = useState<string | null>(null);
  const [status, setStatus] = useState<'loading' | 'ok' | 'anon' | 'error'>('loading');
  const [form, setForm] = useState({ display_name: '', phone: '', bio: '' });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    if (!token) {
      setStatus('anon');
      return;
    }
    try {
      const res = await fetch(`/api/v1/supabase/profile?token=${encodeURIComponent(token)}`);
      const d = (await res.json()) as {
        status?: string;
        profile?: ProfileRow | null;
        wallet?: WalletRow;
        user?: { email?: string };
      };
      if (d.status === 'ok') {
        setProfile(d.profile ?? null);
        setWallet(d.wallet ?? null);
        setEmail(d.user?.email ?? null);
        setForm({
          display_name: d.profile?.display_name ?? '',
          phone: d.profile?.phone ?? '',
          bio: d.profile?.bio ?? '',
        });
        setStatus('ok');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const save = async () => {
    if (!token) return;
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const q = new URLSearchParams({ token, display_name: form.display_name });
      if (form.phone) q.set('phone', form.phone);
      if (form.bio) q.set('bio', form.bio);
      const res = await fetch(`/api/v1/supabase/profile?${q.toString()}`, { method: 'PUT' });
      const d = (await res.json()) as { status?: string; error?: string };
      if (d.status === 'ok') {
        setMsg('پروفایل به‌روزرسانی شد ✅');
        void load();
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
          <UserCircle2 size={17} /> پروفایل کاربر
        </h3>
        {profile?.role && (
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 800,
              padding: '0.2rem 0.55rem',
              borderRadius: 999,
              background: profile.role === 'admin' ? '#fef3c7' : '#ecfdf5',
              color: profile.role === 'admin' ? '#92400e' : '#065f46',
              border: '1px solid var(--color-border)',
            }}
          >
            نقش:{' '}
            {profile.role === 'admin' ? 'مدیر' : profile.role === 'auditor' ? 'ممیزی' : 'کشاورز'}
          </span>
        )}
      </div>

      {status === 'anon' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          برای مشاهده و ویرایش پروفایل وارد شوید.
        </p>
      )}
      {status === 'loading' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>
      )}
      {status === 'error' && (
        <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ خطا در دریافت پروفایل</p>
      )}

      {status === 'ok' && (
        <>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.7rem' }}>
            <div
              style={{
                flex: '1 1 150px',
                padding: '0.55rem 0.7rem',
                borderRadius: 10,
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
              }}
            >
              <div
                style={{
                  fontSize: '0.66rem',
                  color: 'var(--color-text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
              >
                <Wallet size={11} /> موجودی اکو (ECO)
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0d9488' }}>
                {wallet?.eco_balance ?? 0}
              </div>
            </div>
            <div
              style={{
                flex: '1 1 150px',
                padding: '0.55rem 0.7rem',
                borderRadius: 10,
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
              }}
            >
              <div
                style={{
                  fontSize: '0.66rem',
                  color: 'var(--color-text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
              >
                <Wallet size={11} /> اعتبار کربن (CCT)
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0d9488' }}>
                {wallet?.cct_balance ?? 0}
              </div>
            </div>
            <div
              style={{
                flex: '1 1 150px',
                padding: '0.55rem 0.7rem',
                borderRadius: 10,
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
              }}
            >
              <div
                style={{
                  fontSize: '0.66rem',
                  color: 'var(--color-text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
              >
                <BadgeCheck size={11} /> سطح / رتبه
              </div>
              <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0d9488' }}>
                {wallet?.level ?? '—'} · {wallet?.rank ?? 0}
              </div>
            </div>
          </div>

          <div
            style={{
              fontSize: '0.72rem',
              color: 'var(--color-text-secondary)',
              marginBottom: '0.5rem',
            }}
          >
            {email}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.45rem',
            }}
          >
            <label style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              نام نمایشی
              <input
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                placeholder="نام شما"
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: '0.2rem',
                  padding: '0.4rem 0.5rem',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)',
                  color: 'var(--color-text)',
                }}
              />
            </label>
            <label style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              تلفن
              <input
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="09…"
                style={{
                  display: 'block',
                  width: '100%',
                  marginTop: '0.2rem',
                  padding: '0.4rem 0.5rem',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)',
                  color: 'var(--color-text)',
                }}
              />
            </label>
          </div>
          <label
            style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-secondary)',
              display: 'block',
              marginTop: '0.45rem',
            }}
          >
            معرفی
            <textarea
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              rows={2}
              placeholder="کشاورز، دامدار، فعال احیای زمین…"
              style={{
                display: 'block',
                width: '100%',
                marginTop: '0.2rem',
                padding: '0.4rem 0.5rem',
                borderRadius: 8,
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                color: 'var(--color-text)',
                resize: 'vertical',
              }}
            />
          </label>

          <button
            onClick={() => void save()}
            disabled={busy}
            style={{
              marginTop: '0.6rem',
              padding: '0.4rem 1rem',
              borderRadius: 8,
              border: 'none',
              cursor: 'pointer',
              background: 'var(--color-primary)',
              color: '#fff',
              fontWeight: 700,
              fontSize: '0.78rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
            }}
          >
            <Save size={13} /> {busy ? 'در حال ذخیره…' : 'ذخیره پروفایل'}
          </button>
          {msg && (
            <p style={{ fontSize: '0.76rem', color: '#10b981', margin: '0.4rem 0 0' }}>✓ {msg}</p>
          )}
          {err && (
            <p style={{ fontSize: '0.76rem', color: '#ef4444', margin: '0.4rem 0 0' }}>⚠️ {err}</p>
          )}
        </>
      )}
    </div>
  );
};
