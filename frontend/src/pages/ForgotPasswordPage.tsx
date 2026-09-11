import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft } from 'lucide-react';
import Seo from '../components/ui/Seo';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { useToast } from '../components/ui/Toast';
import { getApiBase } from '../lib/api';

const translations = {
  fa: {
    kicker: 'بازیابی رمز عبور',
    title: 'فراموشی رمز عبور',
    subtitle: 'ایمیل خود را وارد کنید تا لینک بازیابی ارسال شود',
    email: 'ایمیل',
    sendLink: 'ارسال لینک بازیابی',
    loading: 'در حال ارسال...',
    backToLogin: 'بازگشت به ورود',
    emailPlaceholder: 'email@example.com',
    success: 'لینک بازیابی ارسال شد',
    checkEmail: 'لینک بازیابی به ایمیل شما ارسال شد.',
    checkEmailDesc: 'لطفاً صندوق ورودی خود را بررسی کنید.',
  },
  en: {
    kicker: 'Password Recovery',
    title: 'Forgot password',
    subtitle: 'Enter your email to receive a reset link',
    email: 'Email',
    sendLink: 'Send reset link',
    loading: 'Sending...',
    backToLogin: 'Back to login',
    emailPlaceholder: 'email@example.com',
    success: 'Reset link sent',
    checkEmail: 'We sent you a password reset link.',
    checkEmailDesc: 'Please check your inbox.',
  },
};

export default function ForgotPasswordPage() {
  const { lang } = useLang();
  const { showToast } = useToast();
  const t = translations[lang as 'fa' | 'en'];

  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const base = getApiBase();
      const response = await fetch(`${base}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error('Failed to send reset link');
      }

      setSent(true);
      showToast({ type: 'success', title: t.success, description: t.checkEmail });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset link');
      showToast({ type: 'error', title: 'Error', description: error });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Seo title={`${t.title} | Eco Nojin`} description={t.subtitle} path="/forgot-password" />
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md">
          <Reveal className="mb-8 text-center">
            <h1 className="text-3xl font-extrabold text-[var(--color-night-100)]">{t.title}</h1>
            <p className="mt-2 text-sm text-[var(--color-night-200)]">{t.subtitle}</p>
          </Reveal>

          <Reveal delay={0.1}>
            {sent ? (
              <div className="glass flex flex-col items-center gap-4 rounded-3xl p-7 text-center">
                <Mail className="h-12 w-12 text-[var(--color-leaf-400)]" />
                <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{t.checkEmail}</h2>
                <p className="text-sm text-[var(--color-night-200)]">{t.checkEmailDesc}</p>
                <Link
                  to="/login"
                  className="mt-2 inline-flex items-center gap-2 text-sm font-extrabold text-[var(--color-leaf-300)] hover:underline"
                >
                  <ArrowLeft className="h-4 w-4" />
                  {t.backToLogin}
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="glass flex flex-col gap-4 rounded-3xl p-7">
                {error && (
                  <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-xs text-red-300">
                    {error}
                  </div>
                )}

                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[var(--color-night-200)]">{t.email}</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={t.emailPlaceholder}
                      required
                      dir="ltr"
                      className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="mt-2 w-full rounded-xl bg-[var(--color-leaf-500)] py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.01] disabled:opacity-50"
                >
                  {isLoading ? t.loading : t.sendLink}
                </button>

                <Link
                  to="/login"
                  className="mt-2 flex items-center justify-center gap-2 text-xs font-extrabold text-[var(--color-leaf-300)] hover:underline"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  {t.backToLogin}
                </Link>
              </form>
            )}
          </Reveal>
        </div>
      </div>
    </>
  );
}