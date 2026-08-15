"use client";
import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Lock, CheckCircle, AlertCircle, Loader2, ArrowRight } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { api } from '../../lib/api-client';

export default function ResetPasswordPage() {
  const { colors } = useTheme();
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) setError('Invalid or missing reset token');
  }, [token]);

  const errors = {
    password: password.length < 6 ? 'Min 6 characters' : null,
    confirm: password !== confirmPassword ? 'Passwords do not match' : null,
  };
  const isFormValid = token && !errors.password && !errors.confirm && password && confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;
    setError(null);
    setLoading(true);
    try {
      const res = await api.post<any>('/api/v1/auth/reset-password', { token, new_password: password });
      if (res.success) {
        setSuccess(true);
        setTimeout(() => router.push('/login?message=Password+reset+successful'), 3000);
      } else {
        setError(res.error || 'Failed to reset');
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div dir="ltr" style={{ background: colors.bg, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          style={{ background: colors.cardBg, padding: '40px', borderRadius: '24px', border: `1px solid ${colors.border}`, maxWidth: '450px', width: '100%', textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: `${colors.success}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
            <CheckCircle size={32} color={colors.success} />
          </div>
          <h1 style={{ color: colors.text, fontSize: '1.5rem', marginBottom: '12px' }}>Password Reset Successfully!</h1>
          <p style={{ color: colors.textMuted, marginBottom: '20px' }}>Redirecting to login...</p>
          <Link href="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '10px 20px', borderRadius: '8px', background: colors.primary, color: 'white', fontWeight: '600', textDecoration: 'none' }}>
            Go to Login <ArrowRight size={16} />
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div dir="ltr" style={{ background: colors.bg, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{ background: colors.cardBg, padding: '40px', borderRadius: '24px', border: `1px solid ${colors.border}`, maxWidth: '450px', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <Lock size={32} color="white" />
          </div>
          <h1 style={{ color: colors.text, fontSize: '1.75rem', fontWeight: '800' }}>Set New Password</h1>
        </div>

        {!token && <div style={{ padding: '12px', background: `${colors.danger}15`, borderRadius: '8px', color: colors.danger, marginBottom: '16px', fontSize: '0.85rem' }}>Invalid reset link.</div>}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: colors.text, marginBottom: '6px', fontWeight: '600' }}>New Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Min 6 characters" required
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${errors.password ? colors.danger : colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
          </div>
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: colors.text, marginBottom: '6px', fontWeight: '600' }}>Confirm</label>
            <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Repeat" required
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${errors.confirm ? colors.danger : colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
          </div>

          {error && <div style={{ padding: '10px', background: `${colors.danger}15`, borderRadius: '8px', color: colors.danger, fontSize: '0.85rem', marginBottom: '12px', display: 'flex', gap: '8px' }}><AlertCircle size={16} /> {error}</div>}

          <motion.button type="submit" whileHover={!loading && isFormValid ? { scale: 1.02 } : {}} disabled={loading || !isFormValid}
            style={{ width: '100%', padding: '14px', borderRadius: '12px', background: loading || !isFormValid ? colors.textMuted : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`, color: 'white', border: 'none', cursor: loading || !isFormValid ? 'not-allowed' : 'pointer', fontWeight: '700', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            {loading ? <><Loader2 size={18} className="animate-spin" /> Resetting...</> : <><Lock size={18} /> Reset Password</>}
          </motion.button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <Link href="/login" style={{ color: colors.primary, fontSize: '0.85rem' }}>Back to login</Link>
        </div>
      </motion.div>

      <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}