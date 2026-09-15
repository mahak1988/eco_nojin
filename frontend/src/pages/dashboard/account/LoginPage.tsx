import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import Seo from '../../../components/ui/Seo';
import { authApi, getToken, setToken, ApiError } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';

/** A1 — login: JWT from /auth/login, stored locally, Authorization header in the API client. */
export default function LoginPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [token, setStored] = useState<string | null>(() => getToken());

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-ink-1 focus:border-leaf-400/60 focus:outline-none';

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus('sending');
    setError(null);
    try {
      const result = await authApi.login({ email: email.trim(), password });
      setToken(result.access_token);
      setStored(result.access_token);
      setStatus('idle');
    } catch (err) {
      setStatus('error');
      setError(
        err instanceof ApiError ? `${err.message} — ${JSON.stringify(err.detail).slice(0, 160)}` : String(err),
      );
    }
  };

  const logout = () => {
    setToken(null);
    setStored(null);
    setEmail('');
    setPassword('');
  };

  return (
    <div className="mx-auto max-w-md">
      <Seo title={`${isFa ? 'ورود' : 'Login'} | ${t.brand.name}`} path="/dashboard/login" />
      <h1 className="text-2xl font-extrabold text-ink-1">{isFa ? 'ورود به داشبورد' : 'Dashboard login'}</h1>

      {token ? (
        <div className="glass mt-5 flex flex-col gap-3 rounded-[21px] p-6">
          <p className="text-sm font-bold text-leaf-300">{isFa ? 'وارد شده‌اید ✓' : 'Signed in ✓'}</p>
          <p className="text-[11px] leading-6 text-ink-3">
            {isFa
              ? 'توکن JWT ذخیره و به‌طور خودکار در هدر Authorization همهٔ فراخوانی‌های زنده (پروفایل کاربر، مدل‌های دارای مجوز) ارسال می‌شود. بایند دائمی کلید هاب به حساب، در فاز بعدی.'
              : 'The JWT is stored and sent automatically in the Authorization header of all live calls (profile, permissioned models). Permanent hub-key binding arrives next phase.'}
          </p>
          <button type="button" onClick={logout} className="w-fit rounded-full bg-white/10 px-4 py-1.5 text-xs font-bold text-ink-2 hover:bg-white/15">
            {isFa ? 'خروج' : 'Log out'}
          </button>
        </div>
      ) : (
        <form onSubmit={submit} className="glass mt-5 flex flex-col gap-4 rounded-[21px] p-6">
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold text-ink-3">{isFa ? 'ایمیل' : 'Email'}</span>
            <input type="email" dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} required />
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold text-ink-3">{isFa ? 'گذرواژه' : 'Password'}</span>
            <input type="password" dir="ltr" value={password} onChange={(e) => setPassword(e.target.value)} className={inputCls} required />
          </label>
          {status === 'error' ? (
            <p role="alert" className="rounded-xl border border-red-400/30 bg-red-400/10 p-3 text-[11px] font-bold text-red-300" dir="ltr">
              {error}
            </p>
          ) : null}
          <button type="submit" disabled={status === 'sending'} className="rounded-xl bg-leaf-500 px-5 py-2.5 text-sm font-extrabold text-night-950 disabled:opacity-60">
            {status === 'sending' ? '…' : isFa ? 'ورود' : 'Sign in'}
          </button>
          <p className="text-[11px] text-ink-3">
            {isFa
              ? 'حساب ندارید؟ از «ثبت‌نام» درگاه استفاده کنید یا با ادمین پروژه هماهنگ کنید.'
              : 'No account? Use the gateway registration endpoint or ask the project admin.'}
          </p>
          <Link to="/dashboard" className="w-fit text-xs font-bold text-aqua-300 hover:underline">
            {isFa ? 'بازگشت به داشبورد' : 'Back to dashboard'}
          </Link>
        </form>
      )}
    </div>
  );
}
