import { useTranslation } from 'react-i18next';
import { APP_DESCRIPTION, APP_NAME } from '@eco/config';
import { BrandMark } from '../components/BrandMark';
import { cn } from '@eco/utils';

const FOOTER_COLS = [
  {
    title: 'محصول',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
    links: [
      { href: '/', label: 'خانه', external: false },
      { href: '/knowledge', label: 'دانش‌نامه', external: false },
      { href: '/models', label: 'مدل‌های علمی', external: false },
      { href: '/dashboard', label: 'داشبورد HyDroMa', external: true },
    ],
  },
  {
    title: 'تخصص‌ها',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" strokeLinejoin="round" />
      </svg>
    ),
    links: [
      { href: '/knowledge#carbon', label: 'کربن خاک (RothC)', external: false },
      { href: '/knowledge#hydrology', label: 'هیدرولوژی (SWAT+)', external: false },
      { href: '/knowledge#crop', label: 'محصول-آب (AquaCrop)', external: false },
      { href: '/knowledge#satellite', label: 'سنجش از دور (Sentinel)', external: false },
    ],
  },
  {
    title: 'منابع',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" strokeLinecap="round" />
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" strokeLinejoin="round" />
      </svg>
    ),
    links: [
      { href: '/knowledge', label: 'مقالات علمی', external: false },
      { href: '/models', label: 'کاتالوگ مدل‌ها', external: false },
      { href: 'https://github.com', label: 'مخزن کد', external: true },
      { href: '/dashboard', label: 'مستندات API', external: false },
    ],
  },
  {
    title: 'سازمان',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="8" r="4" /><path d="M4 20c0-4 4-6 8-6s8 2 8 6" strokeLinejoin="round" />
      </svg>
    ),
    links: [
      { href: '/about', label: 'درباره ما', external: false },
      { href: '/contact', label: 'تماس', external: false },
      { href: '/privacy', label: 'حریم خصوصی', external: false },
      { href: '/terms', label: 'شرایط استفاده', external: false },
    ],
  },
] as const;

export function Footer() {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  return (
    <footer className="relative mt-24 border-t border-ink/10 bg-surface-inverse text-ink-inverse">
      <div className="pointer-events-none absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-brand-400 to-transparent" />

      <div className="mx-auto w-full max-w-content px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-12">
          {/* Brand card */}
          <div className="md:col-span-4">
            <div className="h-full rounded-2xl border border-ink-inverse/10 bg-surface-inverse-muted p-6">
              <div className="flex items-center gap-3 text-ink-inverse">
                <BrandMark size={40} className="drop-shadow-sm" />
                <div className="flex flex-col leading-tight">
                  <span className="text-lg font-semibold">{APP_NAME}</span>
                  <span className="text-[10px] font-medium uppercase tracking-[0.18em] text-ink-inverse/60">
                    اکو نوژین
                  </span>
                </div>
              </div>
              <p className="mt-4 text-sm leading-relaxed text-ink-inverse/70">
                {APP_DESCRIPTION}
              </p>

              <div className="mt-6">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-inverse/60">
                  عضویت در خبرنامه
                </h4>
                <form
                  className="mt-3 flex max-w-sm gap-2"
                  onSubmit={(e) => e.preventDefault()}
                  aria-label="فرم عضویت در خبرنامه"
                >
                  <label htmlFor="newsletter-email" className="sr-only">
                    ایمیل شما
                  </label>
                  <input
                    id="newsletter-email"
                    type="email"
                    required
                    placeholder="ایمیل شما"
                    className="flex-1 rounded-lg border border-ink-inverse/15 bg-surface-inverse px-3 py-2 text-sm text-ink-inverse placeholder:text-ink-inverse/40 focus:border-brand-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                  />
                  <button
                    type="submit"
                    className="rounded-lg bg-gradient-brand px-4 py-2 text-sm font-semibold text-white shadow-soft transition hover:shadow-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                  >
                    عضویت
                  </button>
                </form>
                <p className="mt-2 text-xs text-ink-inverse/50">
                  ماهی یک‌بار، خلاصه‌ای از تازه‌ترین مدل‌ها و داده‌ها.
                </p>
              </div>
            </div>
          </div>

          {/* Link cards */}
          <div className="md:col-span-8">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {FOOTER_COLS.map((col) => (
                <div
                  key={col.title}
                  className="rounded-2xl border border-ink-inverse/10 bg-surface-inverse-muted p-5 transition-all hover:border-ink-inverse/20 hover:shadow-soft"
                >
                  <div className="flex items-center gap-2 text-brand-300">
                    {col.icon}
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-inverse/80">
                      {col.title}
                    </h4>
                  </div>
                  <ul className="mt-4 space-y-2.5 text-sm">
                    {col.links.map((link) => (
                      <li key={link.href}>
                        <a
                          href={link.href}
                          target={link.external ? '_blank' : undefined}
                          rel={link.external ? 'noopener noreferrer' : undefined}
                          className="flex items-center gap-2 text-ink-inverse/75 transition-colors hover:text-brand-300"
                        >
                          <span className="h-1 w-1 rounded-full bg-ink-inverse/30 transition-colors group-hover:bg-brand-400" />
                          {link.label}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom strip */}
        <div className="mt-8 flex flex-col items-center justify-between gap-4 rounded-2xl border border-ink-inverse/10 bg-surface-inverse-muted px-6 py-4 text-xs text-ink-inverse/60 md:flex-row md:items-center">
          <div className="flex items-center gap-2">
            <span>© {year} {APP_NAME}. {t('app.tagline')}</span>
          </div>
          <div className="flex items-center gap-3 text-ink-inverse/70">
            <a href="/privacy" className="transition-colors hover:text-brand-300">حریم خصوصی</a>
            <span className="text-ink-inverse/30">·</span>
            <a href="/terms" className="transition-colors hover:text-brand-300">شرایط</a>
            <span className="text-ink-inverse/30">·</span>
            <a href="/contact" className="transition-colors hover:text-brand-300">تماس</a>
          </div>
          <div className="flex items-center gap-2">
            <span className="rounded-full border border-ink-inverse/15 px-2 py-0.5">v2.0.0-beta</span>
            <span className="rounded-full bg-leaf-700/30 px-2 py-0.5 text-leaf-300">ساخت ایران</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
