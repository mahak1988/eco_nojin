import { useTranslation } from 'react-i18next';
import { APP_DESCRIPTION, APP_NAME } from '@eco/config';
import { BrandMark } from '../components/BrandMark';

const FOOTER_COLS: { title: string; links: { href: string; label: string; external?: boolean }[] }[] = [
  {
    title: 'محصول',
    links: [
      { href: '/', label: 'خانه' },
      { href: '/knowledge', label: 'دانش‌نامه' },
      { href: '/models', label: 'مدل‌های علمی' },
      { href: '/dashboard', label: 'داشبورد HyDroMa' },
    ],
  },
  {
    title: 'تخصص‌ها',
    links: [
      { href: '/knowledge#carbon', label: 'کربن خاک (RothC)' },
      { href: '/knowledge#hydrology', label: 'هیدرولوژی (SWAT+)' },
      { href: '/knowledge#crop', label: 'محصول-آب (AquaCrop)' },
      { href: '/knowledge#satellite', label: 'سنجش از دور (Sentinel)' },
    ],
  },
  {
    title: 'منابع',
    links: [
      { href: '/knowledge', label: 'مقالات علمی' },
      { href: '/models', label: 'کاتالوگ مدل‌ها' },
      { href: 'https://github.com', label: 'مخزن کد', external: true },
      { href: '/dashboard', label: 'مستندات API' },
    ],
  },
  {
    title: 'سازمان',
    links: [
      { href: '/about', label: 'درباره ما' },
      { href: '/contact', label: 'تماس' },
      { href: '/privacy', label: 'حریم خصوصی' },
      { href: '/terms', label: 'شرایط استفاده' },
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
        <div className="grid gap-12 md:grid-cols-12">
          {/* Brand column */}
          <div className="md:col-span-4">
            <div className="flex items-center gap-3 text-ink-inverse">
              <BrandMark size={40} className="drop-shadow-sm" />
              <div className="flex flex-col leading-tight">
                <span className="text-lg font-semibold">{APP_NAME}</span>
                <span className="text-[10px] font-medium uppercase tracking-[0.18em] text-ink-inverse/60">
                  اکو نُژین
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
                  className="flex-1 rounded-lg border border-ink-inverse/15 bg-surface-inverse-muted px-3 py-2 text-sm text-ink-inverse placeholder:text-ink-inverse/40 focus:border-brand-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
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

          {/* Link columns */}
          <div className="grid gap-8 md:col-span-8 md:grid-cols-4">
            {FOOTER_COLS.map((col) => (
              <div key={col.title}>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-inverse/60">
                  {col.title}
                </h4>
                <ul className="mt-4 space-y-3 text-sm">
                  {col.links.map((link) =>
                    link.external ? (
                      <li key={link.href}>
                        <a
                          href={link.href}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-ink-inverse/80 transition-colors hover:text-brand-300"
                        >
                          {link.label}
                        </a>
                      </li>
                    ) : (
                      <li key={link.href}>
                        <a
                          href={link.href}
                          className="text-ink-inverse/80 transition-colors hover:text-brand-300"
                        >
                          {link.label}
                        </a>
                      </li>
                    ),
                  )}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom strip */}
        <div className="mt-12 flex flex-col items-start justify-between gap-4 border-t border-ink-inverse/10 pt-6 text-xs text-ink-inverse/60 md:flex-row md:items-center">
          <div className="flex items-center gap-4">
            <span>© {year} {APP_NAME}. {t('app.tagline')}</span>
          </div>
          <div className="flex items-center gap-3 text-ink-inverse/70">
            <a href="/privacy" className="hover:text-brand-300">حریم خصوصی</a>
            <span>·</span>
            <a href="/terms" className="hover:text-brand-300">شرایط</a>
            <span>·</span>
            <a href="/contact" className="hover:text-brand-300">تماس</a>
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