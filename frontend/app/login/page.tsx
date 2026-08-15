"use client";
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { LogIn, Leaf, Mail, Lock, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { useAuth } from '../../lib/auth-context';

export default function LoginPage() {
  const { colors } = useTheme();
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get('redirect') || '/dashboard';
  const message = searchParams.get('message');

  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(message);

  useEffect(() => {
    if (isAuthenticated) router.push(redirect);
  }, [isAuthenticated, router, redirect]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(formData.email, formData.password);
      if (res.success) {
        router.push(redirect);
      } else {
        setError(res.error || 'Invalid credentials');
      }
    } catch (e: any) {
      setError(e.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (email: string, password: string) => {
    setFormData({ email, password });
    setError(null);
    setLoading(true);
    try {
      const res = await login(email, password);
      if (res.success) {
        router.push('/dashboard');
      } else {
        setError(res.error || 'Demo login failed');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = formData.email && formData.password;

  return (
    <div dir="ltr" style={{ 
      background: `linear-gradient(135deg, ${colors.bg}, ${colors.bgAlt})`,
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px',
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '40px', borderRadius: '24px',
          border: `1px solid ${colors.border}`, maxWidth: '450px', width: '100%',
          boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '16px',
            background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 16px',
          }}>
            <Leaf size={32} color="white" />
          </div>
          <h1 style={{ color: colors.text, fontSize: '1.75rem', fontWeight: '800' }}>Welcome back</h1>
          <p style={{ color: colors.textMuted, fontSize: '0.9rem' }}>Sign in to Eco Nojin</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: colors.text, marginBottom: '6px', fontWeight: '600' }}>Email</label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="email" value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="you@example.com" required autoComplete="email"
                style={{
                  width: '100%', padding: '12px 14px 12px 42px', borderRadius: '10px',
                  border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                  fontSize: '0.95rem', boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: colors.text, marginBottom: '6px', fontWeight: '600' }}>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password" value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢" required autoComplete="current-password"
                style={{
                  width: '100%', padding: '12px 14px 12px 42px', borderRadius: '10px',
                  border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                  fontSize: '0.95rem', boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          <div style={{ textAlign: 'right', marginBottom: '20px' }}>
            <Link href="/forgot-password" style={{ color: colors.primary, fontSize: '0.85rem' }}>
              Forgot password?
            </Link>
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              style={{
                padding: '12px 14px', marginBottom: '16px',
                background: `${colors.danger}15`, border: `1px solid ${colors.danger}40`,
                borderRadius: '10px', color: colors.danger, fontSize: '0.85rem',
                display: 'flex', alignItems: 'center', gap: '8px',
              }}
            >
              <AlertCircle size={16} /> {error}
            </motion.div>
          )}

          <motion.button
            type="submit" whileHover={!loading ? { scale: 1.02 } : {}}
            whileTap={!loading ? { scale: 0.98 } : {}}
            disabled={loading || !isFormValid}
            style={{
              width: '100%', padding: '14px', borderRadius: '12px',
              background: loading || !isFormValid ? colors.textMuted : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
              color: 'white', border: 'none', cursor: loading || !isFormValid ? 'not-allowed' : 'pointer',
              fontWeight: '700', fontSize: '1rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}
          >
            {loading ? <><Loader2 size={18} className="animate-spin" /> Logging in...</> : <><LogIn size={18} /> Login</>}
          </motion.button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', margin: '20px 0' }}>
          <div style={{ flex: 1, height: '1px', background: colors.border }} />
          <span style={{ padding: '0 12px', color: colors.textMuted, fontSize: '0.85rem' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: colors.border }} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {[
            { email: 'farmer@test.com', pw: 'farmer123', label: 'ًںŒ¾ Farmer' },
            { email: 'researcher@test.com', pw: 'research123', label: 'ًں”¬ Researcher' },
            { email: 'org@test.com', pw: 'org123', label: 'ًںڈ¢ Organization' },
            { email: 'admin@test.com', pw: 'admin123', label: 'ًں‘¤ Admin' },
          ].map((acc) => (
            <button key={acc.email} type="button" onClick={() => handleDemoLogin(acc.email, acc.pw)}
              disabled={loading}
              style={{
                padding: '8px', background: colors.bg, color: colors.text,
                border: `1px solid ${colors.border}`, borderRadius: '8px',
                cursor: loading ? 'not-allowed' : 'pointer', fontSize: '0.8rem',
              }}>
              {acc.label}
            </button>
          ))}
        </div>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.9rem', color: colors.textMuted }}>
          Don't have an account?{' '}
          <Link href="/register" style={{ color: colors.primary, fontWeight: '600' }}>Register</Link>
        </div>
      </motion.div>

      <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}