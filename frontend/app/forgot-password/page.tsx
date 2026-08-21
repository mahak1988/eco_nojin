"use client";
import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, ArrowLeft, Send, CheckCircle, Loader2, AlertCircle, Copy } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { api } from '../../lib/api-client';

export default function ForgotPasswordPage() {
  const { colors } = useTheme();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [resetData, setResetData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.post<any>('/api/v1/auth/forgot-password', { email });
      if (res.success) {
        setSent(true);
        setResetData(res.data);
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const copyUrl = () => {
    if (resetData?.reset_url) {
      navigator.clipboard.writeText(resetData.reset_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (sent) {
    return (
      <div dir="ltr" style={{ background: colors.bg, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: colors.cardBg, padding: '40px', borderRadius: '24px', border: `1px solid ${colors.border}`, maxWidth: '500px', width: '100%', textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: `${colors.success}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
            <CheckCircle size={32} color={colors.success} />
          </div>
          <h1 style={{ color: colors.text, fontSize: '1.5rem', marginBottom: '12px' }}>Check your email</h1>
          <p style={{ color: colors.textMuted, marginBottom: '24px' }}>
            If an account exists with <strong>{email}</strong>, we've sent a password reset link.
          </p>

          {resetData?.reset_url && (
            <div style={{ padding: '16px', background: `${colors.warm}10`, border: `1px solid ${colors.warm}30`, borderRadius: '10px', marginBottom: '20px', textAlign: 'left' }}>
              <div style={{ fontSize: '0.75rem', color: colors.warm, marginBottom: '8px', fontWeight: '600' }}>
                🔧 Development Mode - Reset Link:
              </div>
              <div style={{ padding: '10px', background: colors.bg, borderRadius: '6px', fontSize: '0.8rem', fontFamily: 'monospace', color: colors.text, wordBreak: 'break-all', marginBottom: '10px' }}>
                {resetData.reset_url}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={copyUrl} style={{ flex: 1, padding: '8px', borderRadius: '6px', background: colors.warm, color: 'white', border: 'none', cursor: 'pointer', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                  <Copy size={14} /> {copied ? 'Copied!' : 'Copy URL'}
                </button>
                <Link href={resetData.reset_url} style={{ flex: 1, padding: '8px', borderRadius: '6px', background: colors.success, color: 'white', textAlign: 'center', textDecoration: 'none', fontWeight: '600' }}>
                  Open â†’
                </Link>
              </div>
            </div>
          )}

          <Link href="/login" style={{ color: colors.primary, fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <ArrowLeft size={16} /> Back to login
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div dir="ltr" style={{ background: colors.bg, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{ background: colors.cardBg, padding: '40px', borderRadius: '24px', border: `1px solid ${colors.border}`, maxWidth: '450px', width: '100%' }}>
        
        <Link href="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: colors.textMuted, fontSize: '0.85rem', marginBottom: '20px', textDecoration: 'none' }}>
          <ArrowLeft size={16} /> Back to login
        </Link>

        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <Mail size={32} color="white" />
          </div>
          <h1 style={{ color: colors.text, fontSize: '1.75rem', fontWeight: '800' }}>Forgot Password?</h1>
          <p style={{ color: colors.textMuted, fontSize: '0.9rem' }}>Enter your email for a reset link</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: colors.text, marginBottom: '6px', fontWeight: '600' }}>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required
              style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
          </div>

          {error && (
            <div style={{ padding: '10px', background: `${colors.danger}15`, borderRadius: '8px', color: colors.danger, fontSize: '0.85rem', marginBottom: '12px', display: 'flex', gap: '8px' }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          <motion.button type="submit" whileHover={!loading ? { scale: 1.02 } : {}} disabled={loading || !email}
            style={{ width: '100%', padding: '14px', borderRadius: '12px', background: loading || !email ? colors.textMuted : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`, color: 'white', border: 'none', cursor: loading || !email ? 'not-allowed' : 'pointer', fontWeight: '700', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            {loading ? <><Loader2 size={18} className="animate-spin" /> Sending...</> : <><Send size={18} /> Send Reset Link</>}
          </motion.button>
        </form>
      </motion.div>

      <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}