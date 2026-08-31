import React, { useEffect, useState } from 'react';
import { ShieldCheck, Users, BookOpen, FileBadge, LayoutDashboard } from 'lucide-react';

interface AdminUserRow {
  id?: string;
  email?: string;
  username?: string;
  level?: string;
  eco_balance?: number;
}

interface StandardRow {
  name?: string;
  organization?: string;
  category?: string;
}

interface CourseRow {
  id?: string;
  title?: string;
  lesson_count?: number;
}

/**
 * فاز ۸-الف — پنل ادمین و تولید محتوا با داده واقعی Supabase:
 * کاربران، استانداردها (کاتالوگ)، دوره‌های LMS، اعتبارهای صادرشده.
 * دسترسی: RLS — فقط مدیر همه کاربران/اعتبارها را می‌بیند؛ auditor صف ممیزی.
 */
export const AdminCard: React.FC = () => {
  const [token] = useState<string | null>(() => localStorage.getItem('eco_token'));
  const [role, setRole] = useState<string | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [standards, setStandards] = useState<StandardRow[]>([]);
  const [courses, setCourses] = useState<CourseRow[]>([]);
  const [tab, setTab] = useState<'users' | 'content' | 'standards'>('users');
  const [status, setStatus] = useState<'loading' | 'ok' | 'anon' | 'error'>('loading');

  useEffect(() => {
    if (!token) {
      setStatus('anon');
      return;
    }
    let alive = true;
    (async () => {
      try {
        const pr = await fetch(`/api/v1/supabase/profile?token=${encodeURIComponent(token)}`).then(
          (r) => r.json()
        );
        if (!alive) return;
        setRole(pr.profile?.role ?? null);
        if (pr.profile?.role === 'admin') {
          const [ur, sr, cr] = await Promise.all([
            fetch(`/api/v1/supabase/admin/users?token=***)}`).then((r) => r.json()),
            fetch('/api/v1/supabase/standards').then((r) => r.json()),
            fetch('/api/v1/lms/courses').then((r) => r.json()),
          ]);
          if (ur.status === 'ok') setUsers(ur.users ?? []);
          if (sr.status === 'ok') setStandards(sr.rows ?? []);
          if (cr.status === 'ok') setCourses(cr.courses ?? []);
        }
        setStatus('ok');
      } catch {
        if (alive) setStatus('error');
      }
    })();
    return () => {
      alive = false;
    };
  }, [token]);

  const isAdmin = role === 'admin';

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
          <ShieldCheck size={17} /> پنل ادمین و تولید محتوا
        </h3>
        <span style={{ fontSize: '0.72rem', color: 'var(--color-text-secondary)' }}>
          {role ?? '—'}
        </span>
      </div>

      {status === 'anon' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          برای دسترسی به پنل ادمین وارد شوید (نقش مدیر لازم است).
        </p>
      )}
      {status === 'loading' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>در حال دریافت…</p>
      )}
      {status === 'error' && (
        <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ خطا در دریافت داده‌ها</p>
      )}

      {status === 'ok' && !isAdmin && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          نقش فعلی شما «{role}» است — پنل ادمین فقط برای نقش مدیر نمایش داده می‌شود. (ممیزی‌ها صف
          راستی‌آزمایی را در کارت ممیزی می‌بینند.)
        </p>
      )}

      {status === 'ok' && isAdmin && (
        <>
          <div
            style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginBottom: '0.6rem' }}
          >
            {(
              [
                ['users', 'کاربران', Users],
                ['content', 'دوره‌ها (تولید محتوا)', BookOpen],
                ['standards', 'استانداردها', FileBadge],
              ] as const
            ).map(([key, label, Icon]) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                style={{
                  padding: '0.35rem 0.8rem',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: tab === key ? 'var(--color-primary)' : 'var(--color-surface)',
                  color: tab === key ? '#fff' : 'var(--color-text)',
                  cursor: 'pointer',
                  fontSize: '0.74rem',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <Icon size={12} /> {label}
              </button>
            ))}
          </div>

          {tab === 'users' && (
            <div style={{ maxHeight: 260, overflowY: 'auto', fontSize: '0.76rem' }}>
              {users.length === 0 && (
                <p style={{ color: 'var(--color-text-secondary)' }}>کاربری یافت نشد.</p>
              )}
              {users.map((u) => (
                <div
                  key={u.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                    padding: '0.32rem 0.1rem',
                    borderBottom: '1px dashed var(--color-border)',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{u.email}</span>
                  <span style={{ color: 'var(--color-text-secondary)' }}>
                    {u.username} · {u.level} · ECO {u.eco_balance ?? 0}
                  </span>
                </div>
              ))}
            </div>
          )}

          {tab === 'content' && (
            <div style={{ maxHeight: 260, overflowY: 'auto', fontSize: '0.76rem' }}>
              {courses.length === 0 && (
                <p style={{ color: 'var(--color-text-secondary)' }}>دوره‌ای ثبت نشده است.</p>
              )}
              {courses.map((c) => (
                <div
                  key={c.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                    padding: '0.32rem 0.1rem',
                    borderBottom: '1px dashed var(--color-border)',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{c.title}</span>
                  <span style={{ color: 'var(--color-text-secondary)' }}>{c.lesson_count} درس</span>
                </div>
              ))}
              <p
                style={{
                  fontSize: '0.68rem',
                  color: 'var(--color-text-secondary)',
                  margin: '0.5rem 0 0',
                }}
              >
                محتوای دوره‌ها از دیتابیس ابری (lms_courses) خوانده می‌شود — افزودن/ویرایش درس از
                پنل، قدم بعدی.
              </p>
            </div>
          )}

          {tab === 'standards' && (
            <div style={{ maxHeight: 260, overflowY: 'auto', fontSize: '0.76rem' }}>
              {standards.length === 0 && (
                <p style={{ color: 'var(--color-text-secondary)' }}>استانداردی ثبت نشده است.</p>
              )}
              {standards.map((s, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                    padding: '0.32rem 0.1rem',
                    borderBottom: '1px dashed var(--color-border)',
                  }}
                >
                  <span style={{ fontWeight: 600 }}>{s.name}</span>
                  <span style={{ color: 'var(--color-text-secondary)' }}>
                    {s.organization} · {s.category}
                  </span>
                </div>
              ))}
            </div>
          )}

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
            <LayoutDashboard size={11} /> همه داده‌ها واقعی و از Supabase (RLS) — دسترسی غیرمدیر در
            سمت سرور مسدود است.
          </p>
        </>
      )}
    </div>
  );
};
