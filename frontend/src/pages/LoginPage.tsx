import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, Chrome } from 'lucide-react';
import Seo from '../components/ui/Seo';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { getApiBase } from '../lib/api';

const translations = {
  fa: {
    kicker: 'ورود به پلتفرم',
    title: 'خوش آمدید',
    subtitle: 'برای ادامه وارد حساب کاربری خود شوید',
    email: 'ایمیل',
    password: 'رمز عبور',
    login: 'ورود',
    loading: 'در حال ورود...',
    forgotPassword: 'رمز عبور را فراموش کردید؟',
    noAccount: 'حساب کاربری ندارید؟',
    register: 'ثبت‌نام',
    or: 'یا',
    googleLogin: 'ورود با Google',
    githubLogin: 'ورود با GitHub',
    emailPlaceholder: 'email@example.com',
    passwordPlaceholder: '••••••••',
    invalidCredentials: 'ایمیل یا رمز عبور نامعتبر است',
    invalidCredentialsHint: 'حتماً قبلاً ثبت‌نام کرده باشید.',
    success: 'ورود موفقیت‌آمیز',
    emailRequired: 'ایمیل الزامی است',
    emailInvalid: 'لطفاً ایمیل معتبر وارد کنید',
    passwordRequired: 'رمز عبور الزامی است',
    rememberMe: 'من را به یاد داشته باش',
    loginFailed: 'ورود ناموفق بود. لطفاً دوباره تلاش کنید.',
  },
  en: {
    kicker: 'Platform Login',
    title: 'Welcome back',
    subtitle: 'Sign in to your account to continue',
    email: 'Email',
    password: 'Password',
    login: 'Sign in',
    loading: 'Signing in...',
    forgotPassword: 'Forgot password?',
    noAccount: "Don't have an account?",
    register: 'Register',
    or: 'or',
    googleLogin: 'Continue with Google',
    githubLogin: 'Continue with GitHub',
    emailPlaceholder: 'email@example.com',
    passwordPlaceholder: '••••••••',
    invalidCredentials: 'Invalid email or password',
    invalidCredentialsHint: 'Make sure you have already registered.',
    success: 'Login successful',
    emailRequired: 'Email is required',
    emailInvalid: 'Please enter a valid email',
    passwordRequired: 'Password is required',
    rememberMe: 'Remember me',
    loginFailed: 'Login failed. Please try again.',
  },
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function LoginPage() {
  const { lang } = useLang();
  const { login } = useAuth();
  const { showToast } = useToast();
  const location = useLocation();
  const t = translations[lang as 'fa' | 'en'];
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});

  // Handle the OAuth callback on mount — the backend redirected us back here
  // with a ?code=...&provider=... query string.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const provider = params.get('provider') as 'google' | 'github' | 'microsoft' | null;
    const mock = params.get('mock') === 'true';

    if (code && provider) {
      const verifier = localStorage.getItem(`oauth_verifier_${provider}`) || '';
      localStorage.removeItem(`oauth_verifier_${provider}`);
      localStorage.removeItem('oauth_provider');

      (async () => {
        setIsLoading(true);
        try {
          const base = getApiBase();
          const url = `${base}/api/v1/auth/supabase/oauth/callback?code=${encodeURIComponent(
            code,
          )}&code_verifier=${encodeURIComponent(verifier)}&provider=${provider}${mock ? '&mock=true' : ''}`;
          const res = await fetch(url);
          const data = await res.json();
          if (data.status !== 'ok') {
            throw new Error(data.error || 'OAuth callback failed');
          }

          login(data.access_token, {
            id: data.user_id,
            email: data.email,
            full_name: data.full_name,
            role: data.role,
            language: data.language,
          });
          showToast({ type: 'success', title: t.success, description: data.email });
          window.location.href = from;
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'OAuth callback failed';
          setError(msg);
          showToast({ type: 'error', title: 'Error', description: msg });
        } finally {
          setIsLoading(false);
        }
      })();
    }
    // We intentionally only run this on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const validate = (): boolean => {
    const errs: { email?: string; password?: string } = {};
    if (!email.trim()) {
      errs.email = t.emailRequired;
    } else if (!EMAIL_RE.test(email.trim())) {
      errs.email = t.emailInvalid;
    }
    if (!password) {
      errs.password = t.passwordRequired;
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});

    if (!validate()) return;

    setIsLoading(true);

    try {
      const base = getApiBase();
      const response = await fetch(`${base}/api/v1/auth/supabase/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });

      const data = await response.json();
      if (data.status !== 'ok') {
        if (data.http === 401) {
          throw new Error(t.invalidCredentials);
        }
        throw new Error(data.error || t.loginFailed);
      }

      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        language: data.language,
        phone: data.phone,
        country: data.country,
        city: data.city,
      });
      showToast({ type: 'success', title: t.success, description: data.email });
      window.location.href = from;
    } catch (err) {
      const msg = err instanceof Error ? err.message : t.loginFailed;
      setError(msg);
      showToast({ type: 'error', title: 'Error', description: msg });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'github' | 'microsoft') => {
    if (oauthLoading) return;
    setOauthLoading(provider);

    try {
      const base = getApiBase();
      const res = await fetch(
        `${base}/api/v1/auth/supabase/oauth/login?provider=${provider}&redirect_uri=${encodeURIComponent(
          window.location.origin + '/login',
        )}`,
      );
      const data = await res.json();
      if (data.status !== 'ok') {
        throw new Error(data.error || `${provider} OAuth unavailable`);
      }

      // Store the code_verifier so the callback page can use it.
      localStorage.setItem(`oauth_verifier_${provider}`, data.code_verifier);
      localStorage.setItem(`oauth_provider`, provider);

      // Redirect the browser to the Supabase OAuth authorize URL.
      window.location.href = data.url;
    } catch (err) {
      const msg = err instanceof Error ? err.message : `${provider} login failed`;
      setError(msg);
      showToast({ type: 'error', title: 'Error', description: msg });
      setOauthLoading(null);
    }
  };

  return (
    <>
      <Seo title={`${t.title} | Eco Nojin`} description={t.subtitle} path="/login" />
      <div className="flex min-h-screen items-center justify-center px-4">
        <div className="w-full max-w-md">
          <Reveal className="mb-8 text-center">
            <h1 className="text-3xl font-extrabold text-[var(--color-night-100)]">{t.title}</h1>
            <p className="mt-2 text-sm text-[var(--color-night-200)]">{t.subtitle}</p>
          </Reveal>

          <Reveal delay={0.1}>
            <form onSubmit={handleSubmit} className="glass flex flex-col gap-4 rounded-3xl p-7">
              {error && (
                <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-xs">
                  <p className="text-red-300">{error}</p>
                  {error.includes('Invalid') || error.includes('invalid') || error.includes('نامعتبر') ? (
                    <p className="mt-1 text-red-300/70">
                      {t.invalidCredentialsHint}{' '}
                      <Link to="/register" className="font-bold text-[var(--color-leaf-300)] hover:underline">
                        {t.register}
                      </Link>
                    </p>
                  ) : null}
                </div>
              )}

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.email}</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (fieldErrors.email) setFieldErrors({ ...fieldErrors, email: undefined });
                    }}
                    placeholder={t.emailPlaceholder}
                    required
                    dir="ltr"
                    aria-invalid={!!fieldErrors.email}
                    className={`w-full rounded-xl border py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:outline-none ${
                      fieldErrors.email
                        ? 'border-red-500/60 focus:border-red-400'
                        : 'border-[var(--color-night-700)] focus:border-[var(--color-leaf-400)]'
                    }`}
                  />
                </div>
                {fieldErrors.email && (
                  <span className="text-[10px] text-red-400">{fieldErrors.email}</span>
                )}
              </div>

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
                {fieldErrors.password && (
                  <span className="text-[10px] text-red-400">{fieldErrors.password}</span>
                )}
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="h-4 w-4 rounded border-[var(--color-sand-500)] bg-[var(--color-night-900)] text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-400)]"
                  />
                  <span className="text-xs text-[var(--color-night-200)]">{t.rememberMe}</span>
                </label>
                <Link to="/forgot-password" className="text-xs font-bold text-[var(--color-leaf-300)] hover:underline">
                  {t.forgotPassword}
                </Link>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 w-full rounded-xl bg-[var(--color-leaf-500)] py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.01] disabled:opacity-50"
              >
                {isLoading ? t.loading : t.login}
              </button>

              <div className="flex items-center gap-3">
                <div className="h-px flex-1 bg-[var(--color-sand-500)]" />
                <span className="text-[11px] text-[var(--color-night-200)]">{t.or}</span>
                <div className="h-px flex-1 bg-[var(--color-sand-500)]" />
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleOAuth('google')}
                  disabled={oauthLoading === 'google' || isLoading}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2 text-xs font-extrabold text-[var(--color-night-200)] transition-colors hover:bg-white/5 disabled:opacity-50"
                >
                  {oauthLoading === 'google' ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-leaf-400)] border-t-transparent" />
                  ) : (
                    <Chrome className="h-4 w-4" aria-hidden />
                  )}
                  {t.googleLogin}
                </button>
                <button
                  type="button"
                  onClick={() => handleOAuth('github')}
                  disabled={oauthLoading === 'github' || isLoading}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2 text-xs font-extrabold text-[var(--color-night-200)] transition-colors hover:bg-white/5 disabled:opacity-50"
                >
                  {oauthLoading === 'github' ? (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--color-leaf-400)] border-t-transparent" />
                  ) : (
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                  )}
                  {t.githubLogin}
                </button>
              </div>

              <div className="mt-2 flex flex-col gap-2 text-center text-xs text-[var(--color-night-200)]">
                <Link to="/forgot-password" className="font-bold text-[var(--color-leaf-300)] hover:underline">
                  {t.forgotPassword}
                </Link>
                <p>
                  {t.noAccount}{' '}
                  <Link to="/register" className="font-bold text-[var(--color-leaf-300)] hover:underline">
                    {t.register}
                  </Link>
                </p>
              </div>
            </form>
          </Reveal>
        </div>
      </div>
    </>
  );
}