import { Link } from '@tanstack/react-router';
import { APP_DESCRIPTION, APP_NAME, DASHBOARD_URL } from '@eco/config';
import { BrandWordmark } from '../components/BrandMark';

type FooterLink = {
  href: string;
  label: string;
  external?: boolean;
  /** Cross-app link (HyDroMa) */
  crossApp?: boolean;
};

const FOOTER_COLS: { title: string; links: readonly FooterLink[] }[] = [
  {
    title: 'محصول',
    links: [
      { href: '/', label: 'خانه' },
      { href: '/knowledge', label: 'دانشنامه' },
      { href: '/models', label: 'مدل‌های علمی' },
      { href: DASHBOARD_URL, label: 'داشبورد HyDroMa', external: true, crossApp: true },
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
      { href: DASHBOARD_URL, label: 'مستندات API', external: true, crossApp: true },
    ],
  },
  {
    title: 'سازمان',
    links: [
      { href: '/knowledge', label: 'درباره ما' },
      { href: '/knowledge', label: 'تماس' },
      { href: '/knowledge', label: 'حریم خصوصی' },
      { href: '/knowledge', label: 'شرایط استفاده' },
    ],
  },
] as const;

function FooterLinkItem({ link }: { link: FooterLink }) {
  if (link.crossApp) {
    return (
      <a
        href={link.href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-ink-inverse/70 transition-colors hover:text-ink-inverse"
      >
        {link.label} <span aria-hidden="true" className="text-[10px]">↗</span>
      </a>
    );
  }
  if (link.external || link.href.includes('#')) {
    return (
      <a href={link.href} className="text-ink-inverse/70 transition-colors hover:text-ink-inverse">
        {link.label}
      </a>
    );
  }
  return (
    <Link to={link.href as '/'} className="text-ink-inverse/70 transition-colors hover:text-ink-inverse">
      {link.label}
    </Link>
  );
}

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative mt-24 border-t border-ink/10 bg-surface-inverse text-ink-inverse">
      <div className="pointer-events-none absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-brand-400 to-transparent" />

      <div className="mx-auto w-full max-w-content px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-6 md:grid-cols-12">
          {/* Brand card */}
          <div className="md:col-span-4">
            <div className="h-full rounded-2xl border border-ink-inverse/10 bg-surface-inverse-muted p-6">
              <BrandWordmark size="md" variant="dark" />
              <p className="mt-4 text-sm leading-relaxed text-ink-inverse/70">{APP_DESCRIPTION}</p>

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
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-inverse/80">
                    {col.title}
                  </h4>
                  <ul className="mt-4 space-y-2.5 text-sm">
                    {col.links.map((link) => (
                      <li key={`${col.title}-${link.label}`}>
                        <FooterLinkItem link={link} />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t border-ink-inverse/10 pt-6 text-xs text-ink-inverse/50 md:flex-row md:items-center">
          <span>© {year} {APP_NAME} — همهٔ حقوق محفوظ است.</span>
          <span className="flex items-center gap-2">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-leaf-400" aria-hidden="true" />
            ساخته‌شده برای تیم‌های بازسازی سرزمین
          </span>
        </div>
      </div>
    </footer>
  );
}
