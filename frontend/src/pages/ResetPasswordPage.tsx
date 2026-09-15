import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Lock, Check } from 'lucide-react';
import Seo from '../components/ui/Seo';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { useToast } from '../components/ui/Toast';
import { getApiBase } from '../lib/api';

const translations = {
  fa: {
    kicker: 'تغییر رمز عبور',
    title: 'رمز عبور جدید',
    subtitle: 'رمز عبور جدید خود را وارد کنید',
    password: 'رمز عبور جدید',
    confirmPassword: 'تکرار رمز عبور جدید',
    resetPassword: 'تغییر رمز عبور',
    loading: 'در حال تغییر...',
    backToLogin: 'بازگشت به ورود',
    passwordPlaceholder: 'حداقل ۸ کاراکتر',
    confirmPasswordPlaceholder: 'تکرار رمز عبور',
    success: 'رمز عبور تغییر کرد',
    passwordMismatch: 'رمز عبورها مطابقت ندارند',
    passwordTooShort: 'رمز عبور باید حداقل ۸ کاراکتر باشد',
    passwordStrengthWeak: 'ضعیف',
    passwordStrengthMedium: 'متوسط',
    passwordStrengthStrong: 'قوی',
    tokenMissing: 'لینک نامعتبر یا منقضی شده است',
    tokenInvalid: 'لینک بازیابی نامعتبر است',
    resetFailed: 'تغییر رمز عبور ناموفق بود',
    resetSuccess: ' Ramirez عبور با موفقیت تغییر کرد',
    resetSuccessDesc: 'اکنون می‌توانید با رمز عبور جدید وارد شوید.',
  },
  en: {
    kicker: 'Password Reset',
    title: 'New password',
    subtitle: 'Enter your new password below',
    password: 'New password',
    confirmPassword: 'Confirm new password',
    resetPassword: 'Reset password',
    loading: 'Resetting...',
    backToLogin: 'Back to login',
    passwordPlaceholder: 'At least 8 characters',
    confirmPasswordPlaceholder: 'Repeat new password',
    success: 'Password changed successfully',
    passwordMismatch: 'Passwords do not match',
    passwordTooShort: 'Password must be at least 8 characters',
    passwordStrengthWeak: 'Weak',
    passwordStrengthMedium: 'Medium',
    passwordStrengthStrong: 'Strong',
    tokenMissing: 'Invalid or expired reset link',
    tokenInvalid: 'Reset link is invalid',
    resetFailed: 'Failed to reset password',
    resetSuccess: 'Password changed successfully',
    resetSuccessDesc: 'You can now sign in with your new password.',
  },
};

const PASSWORD_MIN = 8;

function passwordStrength(pw: string): { label: string; pct: number; color: string } {
  if (pw.length < PASSWORD_MIN) return { label: '', pct: 0, color: '' };
  let score = 0;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 2) return { label: 'Weak', pct: 33, color: 'bg-red-500' };
  if (score <= 3) return { label: 'Medium', pct: 66, color: 'bg-amber-500' };
  return { label: 'Strong', pct: 100, color: 'bg-[var(--color-leaf-500)]' };
}

export default function ResetPasswordPage() {
  const { lang } = useLang();
  const { showToast } = useToast();
  const t = translations[lang as 'fa' | 'en'];
  const isFa = lang === 'fa';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ password?: string; confirmPassword?: string }>({});
  const [success, setSuccess] = useState(false);

  const strength = passwordStrength(password);

  const validate = (): boolean => {
    const errs: { password?: string; confirmPassword?: string } = {};
    if (password.length < PASSWORD_MIN) {
      errs.password = t.passwordTooShort;
    }
    if (confirmPassword !== password) {
      errs.confirmPassword = t.passwordMismatch;
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});

    if (!validate()) return;

    const token = new URLSearchParams(window.location.search).get('token');
    if (!token) {
      setError(t.tokenMissing);
      return;
    }

    setIsLoading(true);

    try {
      const base = getApiBase();
      const response = await fetch(`${base}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || t.resetFailed);
      }

      setSuccess(true);
      showToast({ type: 'success', title: t.success });
    } catch (err) {
      const msg = err instanceof Error ? err.message : t.resetFailed;
      setError(msg);
      showToast({ type: 'error', title: 'Error', description: msg });
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <>
        <Seo title={`${t.title} | Eco Nojin`} description={t.subtitle} path="/reset-password" />
        <div className="flex min-h-screen items-center justify-center px-4">
          <div className="w-full max-w-md">
            <Reveal className="glass flex flex-col items-center gap-4 rounded-3xl p-7 text-center">
              <Check className="h-12 w-12 text-[var(--color-leaf-400)]" />
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{t.success}</h2>
              <p className="text-sm text-[var(--color-night-200)]">{t.resetSuccessDesc}</p>
              <Link
                to="/login"
                className="mt-2 inline-flex items-center gap-2 text-sm font-extrabold text-[var(--color-leaf-300)] hover:underline"
              >
                {t.backToLogin}
              </Link>
            </Reveal>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Seo title={`${t.title} | Eco Nojin`} description={t.subtitle} path="/reset-password" />
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md">
          <Reveal className="mb-8 text-center">
            <h1 className="text-3xl font-extrabold text-[var(--color-night-100)]">{t.title}</h1>
            <p className="mt-2 text-sm text-[var(--color-night-200)]">{t.subtitle}</p>
          </Reveal>

          <Reveal delay={0.1}>
<form onSubmit={handleSubmit} className="glass flex flex-col gap-4 rounded-3xl p-7">
                {error && (
                  <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-xs text-red-300">
                    {error}
                  </div>
                )}

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[var(--color-night-200)]">{t.password}</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => {
                        setPassword(e.target.value);
                        if (fieldErrors.password) setFieldErrors({ ...fieldErrors, password: undefined });
                      }}
                      placeholder={t.passwordPlaceholder}
                      required
                      minLength={8}
                      dir="ltr"
                      aria-invalid={!!fieldErrors.password}
                      className={`w-full rounded-xl border py-2.5 pl-10 pr-10 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:outline-none ${
                        fieldErrors.password
                          ? 'border-red-500/60 focus:border-red-400'
                          : 'border-[var(--color-night-700)] focus:border-[var(--color-leaf-400)]'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] hover:text-[var(--color-night-100)]"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {/* strength bar */}
                  {password.length > 0 && (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-night-700)]">
                        <div
                          className={`h-full ${strength.color} transition-all duration-300`}
                          style={{ width: `${strength.pct}%` as any }}
                        />
                      </div>
                      {strength.label && (
                        <span className="text-[10px] font-bold text-[var(--color-night-200)]">
                          {isFa
                            ? strength.label === 'Weak' ? t.passwordStrengthWeak
                            : strength.label === 'Medium' ? t.passwordStrengthMedium
                            : t.passwordStrengthStrong
                            : strength.label}
                        </span>
                      )}
                    </div>
                  )}
                  {fieldErrors.password && (
                    <span className="text-[10px] text-red-400">{fieldErrors.password}</span>
                  )}
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[var(--color-night-200)]">{t.confirmPassword}</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                    <input
                      type={showConfirm ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => {
                        setConfirmPassword(e.target.value);
                        if (fieldErrors.confirmPassword) setFieldErrors({ ...fieldErrors, confirmPassword: undefined });
                      }}
                      placeholder={t.confirmPasswordPlaceholder}
                      required
                      minLength={8}
                      dir="ltr"
                      aria-invalid={!!fieldErrors.confirmPassword}
                      className={`w-full rounded-xl border py-2.5 pl-10 pr-10 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:outline-none ${
                        fieldErrors.confirmPassword
                          ? 'border-red-500/60 focus:border-red-400'
                          : 'border-[var(--color-night-700)] focus:border-[var(--color-leaf-400)]'
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm(!showConfirm)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] hover:text-[var(--color-night-100)]"
                      aria-label={showConfirm ? 'Hide password' : 'Show password'}
                    >
                      {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {fieldErrors.confirmPassword && (
                    <span className="text-[10px] text-red-400">{fieldErrors.confirmPassword}</span>
                  )}
                </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 w-full rounded-xl bg-[var(--color-leaf-500)] py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.01] disabled:opacity-50"
              >
                {isLoading ? t.loading : t.resetPassword}
              </button>

              <Link
                to="/login"
                className="mt-2 flex items-center justify-center gap-2 text-xs font-extrabold text-[var(--color-leaf-300)] hover:underline"
              >
                {t.backToLogin}
              </Link>
            </form>
          </Reveal>
        </div>
      </div>
    </>
  );
}