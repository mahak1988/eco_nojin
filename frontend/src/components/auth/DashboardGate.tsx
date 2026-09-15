/** Dashboard gate — shows a login CTA when the user is not authenticated.
 * Authenticated users see the dashboard content directly. */

import { Link } from 'react-router-dom';
import { useLang } from '../../i18n/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useSyncProfile } from '../../hooks/useSyncProfile';
import { Lock, User, LogIn } from 'lucide-react';
import Seo from '../ui/Seo';
import PageHeader from '../sections/PageHeader';
import Reveal from '../ui/Reveal';

const translations = {
  fa: {
    kicker: 'دسترسی نیازمند ورود است',
    title: 'دسترسی به داشبورد نیازمند ورود است',
    lead: 'برای استفاده از محاسبه‌گرهای زنده، مرکز تجمیع داده و تنظیمات داشبورد، ابتدا وارد حساب کاربری خود شوید.',
    login: 'ورود به پلتفرم',
    register: 'ثبت‌نام',
    features: [
      'محاسبه‌گرهای زندهٔ مدل‌های علمی هیدروما',
      'ذخیرهٔ اجراها در مرکز تجمیع و اشتراک‌گذاری',
      'سفارشی‌سازی داشبورد (نمایش/پنهان‌سازی بخش‌ها)',
      'دسترسی به تنظیمات API و زبان',
    ],
  },
  en: {
    kicker: 'Access required',
    title: 'Sign in to access the dashboard',
    lead: 'Live calculators, the data hub, and dashboard customization require an account.',
    login: 'Sign in to the platform',
    register: 'Create an account',
    features: [
      'Live scientific model calculators',
      'Save runs to the hub and share them',
      'Customize the dashboard (show/hide sections)',
      'API and language settings',
    ],
  },
};

/** Wraps dashboard content — unauthenticated users see a login CTA instead. */
export default function DashboardGate({ children }: { children: React.ReactNode }) {
  const { lang } = useLang();
  const { isAuthenticated, isLoading } = useAuth();
  const t = translations[lang as 'fa' | 'en'];

  // Sync the full profile from Supabase on mount so the user object
  // (full_name, role, language, phone, country, city, address) is populated
  // for the dashboard and profile page.
  useSyncProfile();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--color-leaf-500)] border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <Seo
          title={`${t.title} | Eco Nojin`}
          description={t.lead}
          path="/dashboard"
        />
        <PageHeader kicker={t.kicker} title={t.title} lead={t.lead} />
        <div className="mx-auto max-w-3xl">
          <Reveal className="glass flex flex-col gap-6 rounded-3xl p-8 sm:p-10">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]">
                <Lock className="h-6 w-6" aria-hidden />
              </span>
              <div>
                <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">
                  {lang === 'fa' ? 'امنیت داشبورد' : 'Secure access'}
                </h2>
                <p className="text-xs text-[var(--color-night-200)]/55">
                  {lang === 'fa'
                    ? 'برای حفظ داده‌های شما و جلوگیری از دسترسی غیرمجاز'
                    : 'Protecting your data and preventing unauthorized access'}
                </p>
              </div>
            </div>

            <ul className="flex flex-col gap-3">
              {t.features.map((feature) => (
                <li key={feature} className="flex items-center gap-3 text-sm text-[var(--color-night-200)]/75">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-aqua-500)]/12 text-[var(--color-aqua-300)]">
                    <User className="h-3.5 w-3.5" aria-hidden />
                  </span>
                  {feature}
                </li>
              ))}
            </ul>

            <div className="flex flex-wrap gap-3">
              <Link
                to="/login"
                className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-6 py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.02]"
              >
                <LogIn className="h-4 w-4" aria-hidden />
                {t.login}
              </Link>
              <Link
                to="/register"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-2.5 text-sm font-extrabold text-[var(--color-night-100)] hover:bg-white/5"
              >
                {t.register}
              </Link>
            </div>
          </Reveal>
        </div>
      </>
    );
  }

  return <>{children}</>;
}