"use client";
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../lib/auth-context';
import { useTheme } from '../../lib/theme-context';
import { X, Mail, Lock, User as UserIcon, LogIn, UserPlus, Leaf } from 'lucide-react';

interface Props { isOpen: boolean; onClose: () => void; initialMode?: 'login' | 'register'; }

export default function AuthModal({ isOpen, onClose, initialMode = 'login' }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login, register } = useAuth();
  const { colors } = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    let res;
    if (mode === 'login') {
      res = await login(email, password);
    } else {
      res = await register(email, password, fullName);
    }
    if (res.success) {
      onClose();
      setEmail(''); setPassword(''); setFullName('');
    } else {
      setError(res.error || 'Failed');
    }
    setLoading(false);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(8px)', zIndex: 2000,
            }}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            style={{
              position: 'fixed', top: '50%', left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 'min(450px, 90vw)',
              background: colors.bgAlt,
              borderRadius: '24px', padding: '40px',
              boxShadow: '0 24px 64px rgba(0,0,0,0.3)',
              zIndex: 2001,
            }}
          >
            <button onClick={onClose} style={{
              position: 'absolute', top: '16px', right: '16px',
              width: '36px', height: '36px', borderRadius: '50%',
              border: 'none', background: colors.bg,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer',
            }}>
              <X size={18} color={colors.text} />
            </button>

            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
              <div style={{
                width: '64px', height: '64px', margin: '0 auto 16px',
                borderRadius: '20px',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: `0 8px 24px ${colors.primary}40`,
              }}>
                <Leaf size={32} color="white" />
              </div>
              <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: colors.text, margin: 0 }}>
                {mode === 'login' ? 'Welcome Back' : 'Join the Movement'}
              </h2>
              <p style={{ color: colors.textMuted, marginTop: '8px', fontSize: '0.9rem' }}>
                {mode === 'login' ? 'Login to your account' : 'Start restoring your land today'}
              </p>
            </div>

            <form onSubmit={handleSubmit}>
              {mode === 'register' && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', fontSize: '0.875rem', color: colors.textMuted, marginBottom: '6px' }}>
                    Full Name
                  </label>
                  <div style={{ position: 'relative' }}>
                    <UserIcon size={16} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input value={fullName} onChange={(e) => setFullName(e.target.value)}
                      required style={{
                        width: '100%', padding: '12px 14px 12px 40px', borderRadius: '10px',
                        border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                        fontFamily: 'inherit', fontSize: '0.95rem',
                      }} />
                  </div>
                </div>
              )}

              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', color: colors.textMuted, marginBottom: '6px' }}>
                  Email
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={16} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    required style={{
                      width: '100%', padding: '12px 14px 12px 40px', borderRadius: '10px',
                      border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                      fontFamily: 'inherit', fontSize: '0.95rem',
                    }} />
                </div>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.875rem', color: colors.textMuted, marginBottom: '6px' }}>
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={16} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                    required minLength={6} style={{
                      width: '100%', padding: '12px 14px 12px 40px', borderRadius: '10px',
                      border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text,
                      fontFamily: 'inherit', fontSize: '0.95rem',
                    }} />
                </div>
              </div>

              {error && (
                <div style={{
                  padding: '12px', background: `${colors.danger}15`,
                  border: `1px solid ${colors.danger}30`,
                  borderRadius: '10px', color: colors.danger,
                  fontSize: '0.875rem', marginBottom: '16px',
                }}>
                  {error}
                </div>
              )}

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit" disabled={loading}
                style={{
                  width: '100%', padding: '14px',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: 'white', border: 'none', borderRadius: '10px',
                  fontWeight: '600', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  fontSize: '1rem',
                  boxShadow: `0 8px 24px ${colors.primary}40`,
                }}
              >
                {mode === 'login' ? <LogIn size={18} /> : <UserPlus size={18} />}
                {loading ? 'Please wait...' : (mode === 'login' ? 'Login' : 'Create Account')}
              </motion.button>
            </form>

            <div style={{ textAlign: 'center', marginTop: '24px', color: colors.textMuted, fontSize: '0.9rem' }}>
              {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
              <button
                onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}
                style={{
                  background: 'none', border: 'none', color: colors.primary,
                  fontWeight: '600', cursor: 'pointer', fontFamily: 'inherit',
                }}
              >
                {mode === 'login' ? 'Register' : 'Login'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
