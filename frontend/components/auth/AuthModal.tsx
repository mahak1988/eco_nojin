"use client";
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../lib/auth-context';
import { useTheme } from '../../lib/theme-context';
import { X, Mail, Lock, User as UserIcon, LogIn, UserPlus, Leaf, Eye, EyeOff } from 'lucide-react';

interface Props { isOpen: boolean; onClose: () => void; initialMode?: 'login' | 'register'; }

export default function AuthModal({ isOpen, onClose, initialMode = 'login' }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const { login, register } = useAuth();
  const { colors } = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // اعتبارسنجی ساده در سمت کلاینت
    if (mode === 'register' && password !== confirmPassword) {
      setError('رمز عبور و تکرار آن یکسان نیستند.');
      return;
    }

    setLoading(true);
    let res;
    if (mode === 'login') {
      res = await login(email, password);
    } else {
      res = await register(email, password, fullName);
    }
    if (res.success) {
      onClose();
      setEmail(''); setPassword(''); setConfirmPassword(''); setFullName('');
    } else {
      setError(res.error || 'عملیات ناموفق بود.');
    }
    setLoading(false);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            style={{
              position: 'fixed', inset: 0,
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(12px)',
              zIndex: 2000,
            }}
          />
          
          {/* Modal Panel with Glassmorphism */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 30 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 30 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            style={{
              position: 'fixed', top: '50%', left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 'min(440px, 92vw)',
              background: colors.cardBg + 'dd',
              backdropFilter: 'blur(20px)',
              borderRadius: '28px',
              padding: '36px 32px',
              border: `1px solid ${colors.border}`,
              boxShadow: '0 25px 60px rgba(0,0,0,0.3)',
              zIndex: 2001,
            }}
          >
            {/* Close Button */}
            <button onClick={onClose} style={{
              position: 'absolute', top: '14px', right: '14px',
              width: '36px', height: '36px', borderRadius: '50%',
              border: 'none', background: colors.bg,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', color: colors.textMuted,
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = colors.text)}
            onMouseOut={(e) => (e.currentTarget.style.color = colors.textMuted)}
            >
              <X size={18} />
            </button>

            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '28px' }}>
              <div style={{
                width: '64px', height: '64px', margin: '0 auto 14px',
                borderRadius: '20px',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: `0 8px 24px ${colors.primary}40`,
              }}>
                <Leaf size={32} color="white" />
              </div>
              <h2 style={{ fontSize: '1.75rem', fontWeight: '800', color: colors.text, margin: 0 }}>
                {mode === 'login' ? 'خوش آمدید' : 'به جمع ما بپیوندید'}
              </h2>
              <p style={{ color: colors.textMuted, marginTop: '6px', fontSize: '0.9rem' }}>
                {mode === 'login' ? 'برای دسترسی به داشبورد وارد شوید' : 'احیای سرزمین خود را همین حالا شروع کنید'}
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {mode === 'register' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: '6px', fontWeight: '500' }}>
                    نام و نام خانوادگی
                  </label>
                  <div style={{ position: 'relative' }}>
                    <UserIcon size={18} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                      placeholder="نام خود را وارد کنید"
                      style={{
                        width: '100%', padding: '12px 14px 12px 44px', borderRadius: '12px',
                        border: `1px solid ${colors.border}`,
                        background: colors.bg, color: colors.text,
                        fontFamily: 'inherit', fontSize: '0.95rem',
                        outline: 'none', transition: 'all 0.2s ease',
                      }}
                      onFocus={(e) => { e.currentTarget.style.borderColor = colors.primary; e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.primary}30`; }}
                      onBlur={(e) => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.boxShadow = 'none'; }}
                    />
                  </div>
                </div>
              )}

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: '6px', fontWeight: '500' }}>
                  ایمیل
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={18} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="example@eco-nojin.com"
                    style={{
                      width: '100%', padding: '12px 14px 12px 44px', borderRadius: '12px',
                      border: `1px solid ${colors.border}`,
                      background: colors.bg, color: colors.text,
                      fontFamily: 'inherit', fontSize: '0.95rem',
                      outline: 'none', transition: 'all 0.2s ease',
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = colors.primary; e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.primary}30`; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.boxShadow = 'none'; }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: '6px', fontWeight: '500' }}>
                  رمز عبور
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    placeholder="حداقل ۶ کاراکتر"
                    style={{
                      width: '100%', padding: '12px 44px 12px 44px', borderRadius: '12px',
                      border: `1px solid ${colors.border}`,
                      background: colors.bg, color: colors.text,
                      fontFamily: 'inherit', fontSize: '0.95rem',
                      outline: 'none', transition: 'all 0.2s ease',
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = colors.primary; e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.primary}30`; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.boxShadow = 'none'; }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      position: 'absolute', right: '14px', top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', cursor: 'pointer', color: colors.textMuted,
                      padding: '0', display: 'flex', alignItems: 'center',
                    }}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: '6px', fontWeight: '500' }}>
                    تکرار رمز عبور
                  </label>
                  <div style={{ position: 'relative' }}>
                    <Lock size={18} color={colors.textMuted} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      placeholder="رمز را دوباره وارد کنید"
                      style={{
                        width: '100%', padding: '12px 44px', borderRadius: '12px',
                        border: `1px solid ${colors.border}`,
                        background: colors.bg, color: colors.text,
                        fontFamily: 'inherit', fontSize: '0.95rem',
                        outline: 'none', transition: 'all 0.2s ease',
                      }}
                      onFocus={(e) => { e.currentTarget.style.borderColor = colors.primary; e.currentTarget.style.boxShadow = `0 0 0 3px ${colors.primary}30`; }}
                      onBlur={(e) => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.boxShadow = 'none'; }}
                    />
                  </div>
                </div>
              )}

              {/* Error Box */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  style={{
                    padding: '12px 16px', background: `${colors.danger}15`,
                    border: `1px solid ${colors.danger}30`,
                    borderRadius: '12px', color: colors.danger,
                    fontSize: '0.875rem', fontWeight: '500',
                  }}
                >
                  {error}
                </motion.div>
              )}

              {/* Submit Button */}
              <motion.button
                whileHover={{ scale: 1.02, boxShadow: `0 8px 30px ${colors.primary}50` }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={loading}
                style={{
                  width: '100%', padding: '14px', marginTop: '8px',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: 'white', border: 'none', borderRadius: '14px',
                  fontWeight: '700', cursor: loading ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                  fontSize: '1rem', opacity: loading ? 0.7 : 1,
                  boxShadow: `0 4px 16px ${colors.primary}40`,
                }}
              >
                {mode === 'login' ? <LogIn size={18} /> : <UserPlus size={18} />}
                {loading ? 'لطفاً صبر کنید...' : (mode === 'login' ? 'ورود به حساب' : 'ایجاد حساب کاربری')}
              </motion.button>
            </form>

            {/* Switch Mode */}
            <div style={{ textAlign: 'center', marginTop: '24px', color: colors.textMuted, fontSize: '0.9rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px' }}>
              {mode === 'login' ? 'حساب کاربری ندارید؟' : 'قبلاً ثبت‌نام کرده‌اید؟'}
              <button
                onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); setPassword(''); setConfirmPassword(''); }}
                style={{
                  background: 'none', border: 'none', color: colors.primary,
                  fontWeight: '700', cursor: 'pointer', fontFamily: 'inherit',
                  fontSize: '0.9rem', padding: '4px 8px', borderRadius: '6px',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => (e.currentTarget.style.background = `${colors.primary}20`)}
                onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                {mode === 'login' ? 'ثبت‌نام' : 'ورود'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}