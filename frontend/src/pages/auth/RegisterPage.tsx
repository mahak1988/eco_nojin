import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthShell, Field } from './AuthShell';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

const roles = [
  { id: 'farmer', label: 'کشاورز' },
  { id: 'rancher', label: 'دامدار' },
  { id: 'researcher', label: 'پژوهشگر' },
  { id: 'student', label: 'دانشجو' },
  { id: 'business', label: 'تجاری' },
  { id: 'org', label: 'سازمانی' },
];

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: '', email: '', phone: '', role: 'farmer', pass: '', confirm: '' });
  const [terms, setTerms] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.pass !== form.confirm) { setError('رمز عبور و تکرار آن یکسان نیست'); return; }
    if (!terms) { setError('لطفاً قوانین و حریم خصوصی را بپذیرید'); return; }
    setError(''); setBusy(true);
    try {
      await register({ name: form.name, email: form.email, role: form.role, password: form.pass });
      navigate('/hydroma');
    } catch (err: any) { setError(err.message); } finally { setBusy(false); }
  };

  return (
    <AuthShell title="ایجاد حساب رایگان" subtitle="کشاورز، دامدار، پژوهشگر یا دانشجو — همه رایگان">
      <form onSubmit={submit}>
        {error && <div className="badge badge-error" style={{ width: '100%', justifyContent: 'center', marginBottom: '1rem', padding: '0.6rem' }}>{error}</div>}

        <Field label="نام و نام خانوادگی">
          <input className="input" required value={form.name} onChange={e => set('name', e.target.value)} placeholder="مثلاً: سارا محمدی" />
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <Field label="ایمیل">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="email" required value={form.email} onChange={e => set('email', e.target.value)} placeholder="you@farm.ir" />
          </Field>
          <Field label="موبایل">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="tel" value={form.phone} onChange={e => set('phone', e.target.value)} placeholder="+98 9xx xxx xxxx" />
          </Field>
        </div>

        <Field label="نقش شما">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            {roles.map(r => (
              <button key={r.id} type="button" onClick={() => set('role', r.id)}
                className={form.role === r.id ? 'btn btn-primary' : 'btn btn-secondary'}
                style={{ padding: '0.6rem 0.4rem', fontSize: '0.8rem' }}>
                {r.label}
              </button>
            ))}
          </div>
        </Field>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <Field label="رمز عبور">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="password" required minLength={8} value={form.pass} onChange={e => set('pass', e.target.value)} />
          </Field>
          <Field label="تکرار رمز">
            <input className="input" dir="ltr" style={{ textAlign: 'left' }} type="password" required minLength={8} value={form.confirm} onChange={e => set('confirm', e.target.value)} />
          </Field>
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginBottom: '1.4rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={terms} onChange={e => setTerms(e.target.checked)} />
          <span><Link to="/terms" style={{ color: 'var(--color-primary)' }}>قوانین</Link> و <Link to="/privacy" style={{ color: 'var(--color-primary)' }}>حریم خصوصی</Link> را می‌پذیرم</span>
        </label>

        <Button variant="primary" size="lg" loading={busy} style={{ width: '100%' }}>ثبت‌نام</Button>

        <p style={{ textAlign: 'center', marginTop: '1.4rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
          حساب دارید؟ <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>ورود</Link>
        </p>
      </form>
    </AuthShell>
  );
};
