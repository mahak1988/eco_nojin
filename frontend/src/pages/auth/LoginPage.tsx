import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, Loader2, Wallet, Globe } from 'lucide-react';
import { AuthShell, Field } from './AuthShell';
import { Button } from '../../components/ui/Button';
import { useAuth } from '../../context/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from || '/hydroma';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setBusy(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message);
    } finally { setBusy(false); }
  };

  return (
    <AuthShell title="خوش آمدید" subtitle="برای دسترسی به ماژول‌ها وارد شوید">
      <form onSubmit={submit}>
        {error && <div className="badge badge-error" style={{ width: '100%', justifyContent: 'center', marginBottom: '1rem', padding: '0.6rem' }}>{error}</div>}

        <Field label="ایمیل">
          <div style={{ position: 'relative' }}>
            <Mail size={16} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
            <input className="input" dir="ltr" style={{ paddingRight: '2.4rem', textAlign: 'left' }} type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@farm.ir" />
          </div>
        </Field>

        <Field label="رمز عبور">
          <div style={{ position: 'relative' }}>
            <Lock size={16} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
            <input className="input" dir="ltr" style={{ paddingRight: '2.4rem', paddingLeft: '2.4rem', textAlign: 'left' }} type={showPass ? 'text' : 'password'} required minLength={6} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            <button type="button" onClick={() => setShowPass(!showPass)} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-tertiary)' }}>
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </Field>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.4rem', fontSize: '0.85rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
            <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
            مرا به خاطر بسپار
          </label>
          <Link to="/forgot-password" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>فراموشی رمز؟</Link>
        </div>

        <Button variant="primary" size="lg" loading={busy} style={{ width: '100%' }}>
          {!busy && <Lock size={16} />} ورود به حساب
        </Button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '1.4rem 0', color: 'var(--color-text-tertiary)', fontSize: '0.8rem' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} /> یا <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <Button variant="secondary" icon={<Globe size={16} />}>Google</Button>
          <Button variant="secondary" icon={<Wallet size={16} />}>Wallet</Button>
        </div>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
          حساب ندارید؟ <Link to="/register" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>ثبت‌نام رایگان</Link>
        </p>
      </form>
    </AuthShell>
  );
};
