import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Check } from 'lucide-react';
import Seo from '../components/ui/Seo';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { useToast } from '../components/ui/Toast';
import { getApiBase } from '../lib/api';

const translations = {
  fa: {
    kicker: 'ایجاد حساب',
    title: 'ثبت‌نام',
    subtitle: 'برای شروع در اکونوژین حساب کاربری ایجاد کنید',
    fullName: 'نام و نام خانوادگی',
    email: 'ایمیل',
    password: 'رمز عبور',
    confirmPassword: 'تکرار رمز عبور',
    register: 'ثبت‌نام',
    loading: 'در حال ثبت‌نام...',
    hasAccount: 'قبلاً حساب کاربری دارید؟',
    login: 'ورود',
    fullNamePlaceholder: 'نام و نام خانوادگی',
    emailPlaceholder: 'email@example.com',
    passwordPlaceholder: 'حداقل ۸ کاراکتر',
    confirmPasswordPlaceholder: 'تکرار رمز عبور',
    success: 'ثبت‌نام موفقیت‌آمیز',
    termsText: 'با ثبت‌نام، قوانین و مقررات را می‌پذیرید',
    passwordRequirements: [
      'حداقل ۸ کاراکتر',
      'حداقل یک حرف بزرگ',
      'حداقل یک عدد',
      'حداقل یک حرف خاص',
    ],
    acceptTerms: 'قوانین و مقررات را می‌پذیرم',
    acceptPrivacy: 'سیاست حریم خصوصی را می‌پذیرم',
  },
  en: {
    kicker: 'Create Account',
    title: 'Sign up',
    subtitle: 'Create your Eco Nojin account to get started',
    fullName: 'Full name',
    email: 'Email',
    password: 'Password',
    confirmPassword: 'Confirm password',
    register: 'Sign up',
    loading: 'Creating account...',
    hasAccount: 'Already have an account?',
    login: 'Sign in',
    fullNamePlaceholder: 'John Doe',
    emailPlaceholder: 'email@example.com',
    passwordPlaceholder: 'At least 8 characters',
    confirmPasswordPlaceholder: 'Repeat password',
    success: 'Registration successful',
    termsText: 'By signing up, you agree to our Terms and Privacy Policy',
    passwordRequirements: [
      'At least 8 characters',
      'At least one uppercase letter',
      'At least one number',
      'At least one special character',
    ],
    acceptTerms: 'I accept the Terms of Service',
    acceptPrivacy: 'I accept the Privacy Policy',
  },
};

export default function RegisterPage() {
  const { lang } = useLang();
  const { showToast } = useToast();
  const t = translations[lang as 'fa' | 'en'];

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
    acceptPrivacy: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!formData.acceptTerms || !formData.acceptPrivacy) {
      setError('You must accept both terms and privacy policy');
      return;
    }

    setIsLoading(true);

    try {
      const base = getApiBase();
      const response = await fetch(`${base}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          full_name: formData.fullName,
          password: formData.password,
          accept_tos: formData.acceptTerms,
          accept_privacy: formData.acceptPrivacy,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Registration failed');
      }

      const data = await response.json();
      localStorage.setItem('auth_token', data.access_token);
      showToast({ type: 'success', title: t.success, description: data.user?.email });
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
      showToast({ type: 'error', title: 'Error', description: error });
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength = formData.password.length >= 8 && /[A-Z]/.test(formData.password) && /[0-9]/.test(formData.password);

  return (
    <>
      <Seo title={`${t.title} | Eco Nojin`} description={t.subtitle} path="/register" />
      <div className="flex min-h-screen items-center justify-center px-4 py-10">
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
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.fullName}</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="text"
                    value={formData.fullName}
                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                    placeholder={t.fullNamePlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.email}</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder={t.emailPlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.password}</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder={t.passwordPlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-10 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
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
                {formData.password && (
                  <div className="flex flex-col gap-1">
                    {t.passwordRequirements.map((req, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <Check className={`h-3 w-3 ${passwordStrength ? 'text-[var(--color-leaf-300)]' : 'text-[var(--color-night-200)]'}`} />
                        <span className="text-[11px] text-[var(--color-night-200)]">{req}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.confirmPassword}</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    placeholder={t.confirmPasswordPlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.acceptTerms}
                    onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
                    className="h-4 w-4 rounded border-[var(--color-sand-500)] bg-[var(--color-night-900)] text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-400)]"
                  />
                  <span className="text-xs text-[var(--color-night-200)]">{t.acceptTerms}</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.acceptPrivacy}
                    onChange={(e) => setFormData({ ...formData, acceptPrivacy: e.target.checked })}
                    className="h-4 w-4 rounded border-[var(--color-sand-500)] bg-[var(--color-night-900)] text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-400)]"
                  />
                  <span className="text-xs text-[var(--color-night-200)]">{t.acceptPrivacy}</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={isLoading || !formData.acceptTerms || !formData.acceptPrivacy}
                className="mt-2 w-full rounded-xl bg-[var(--color-leaf-500)] py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.01] disabled:opacity-50"
              >
                {isLoading ? t.loading : t.register}
              </button>

              <p className="mt-2 text-center text-xs text-[var(--color-night-200)]">
                {t.hasAccount}{' '}
                <Link to="/login" className="font-bold text-[var(--color-leaf-300)] hover:underline">
                  {t.login}
                </Link>
              </p>
            </form>
          </Reveal>
        </div>
      </div>
    </>
  );
}