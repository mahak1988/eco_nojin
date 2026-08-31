import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, CheckCircle2 } from 'lucide-react';
import { AuthShell, Field } from './AuthShell';
import { Button } from '../../components/ui/Button';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    await new Promise((r) => setTimeout(r, 900));
    setBusy(false);
    setSent(true);
  };

  return (
    <AuthShell title="بازیابی رمز عبور" subtitle="لینک بازیابی به ایمیل شما ارسال می‌شود">
      {sent ? (
        <div style={{ textAlign: 'center', padding: '1rem 0' }}>
          <CheckCircle2
            size={56}
            className="animate-float"
            style={{ color: 'var(--color-success)', margin: '0 auto 1rem' }}
          />
          <h3 style={{ marginBottom: '0.5rem' }}>ایمیل ارسال شد</h3>
          <p
            style={{
              color: 'var(--color-text-secondary)',
              fontSize: '0.9rem',
              marginBottom: '1.5rem',
            }}
          >
            لینک بازیابی به {email} ارسال شد. صندوق ورودی را بررسی کنید.
          </p>
          <Link to="/login">
            <Button variant="primary" style={{ width: '100%' }}>
              بازگشت به ورود
            </Button>
          </Link>
        </div>
      ) : (
        <form onSubmit={submit}>
          <Field label="ایمیل ثبت‌شده">
            <div style={{ position: 'relative' }}>
              <Mail
                size={16}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--color-text-tertiary)',
                }}
              />
              <input
                className="input"
                dir="ltr"
                style={{ paddingRight: '2.4rem', textAlign: 'left' }}
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@farm.ir"
              />
            </div>
          </Field>
          <Button variant="primary" size="lg" loading={busy} style={{ width: '100%' }}>
            ارسال لینک بازیابی
          </Button>
          <p style={{ textAlign: 'center', marginTop: '1.4rem', fontSize: '0.9rem' }}>
            <Link to="/login" style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
              بازگشت به ورود
            </Link>
          </p>
        </form>
      )}
    </AuthShell>
  );
};
