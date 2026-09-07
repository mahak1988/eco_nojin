import { Link } from '@tanstack/react-router';
import { APP_NAME, DASHBOARD_URL } from '@eco/config';
import { BrandWordmark } from '../components/BrandMark';

type FooterLink = {
  href: string;
  label: string;
  external?: boolean;
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
  const cls = 'text-xs text-ink-muted transition-colors hover:text-ink hover:underline';
  if (link.crossApp) {
    return (
      <a href={link.href} target="_blank" rel="noopener noreferrer" className={cls}>
        {link.label} <span aria-hidden="true" className="text-[10px]">↗</span>
      </a>
    );
  }
  if (link.external || link.href.includes('#')) {
    return <a href={link.href} className={cls}>{link.label}</a>;
  }
  return (
    <Link to={link.href as '/'} className={cls}>
      {link.label}
    </Link>
  );
}

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-ink/10 bg-surface-muted text-ink">
      <div className="mx-auto w-full max-w-content px-4 py-12 sm:px-6 lg:px-8">
        {/* Brand row */}
        <div className="flex flex-col items-start justify-between gap-6 border-b border-ink/10 pb-8 md:flex-row md:items-center">
          <BrandWordmark size="sm" />
          <p className="max-w-md text-xs leading-relaxed text-ink-muted">
            دوقلوی دیجیتال علمی برای بازسازی سرزمین — مدل‌سازی آب، خاک، کربن و محصول با پایش ماهواره‌ای.
          </p>
        </div>

        {/* Link columns */}
        <div className="grid gap-8 border-b border-ink/10 py-10 sm:grid-cols-2 lg:grid-cols-4">
          {FOOTER_COLS.map((col) => (
            <div key={col.title}>
              <h4 className="text-xs font-semibold text-ink">{col.title}</h4>
              <ul className="mt-4 space-y-3">
                {col.links.map((link) => (
                  <li key={`${col.title}-${link.label}`}>
                    <FooterLinkItem link={link} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom line */}
        <div className="flex flex-col items-start justify-between gap-3 pt-6 text-xs text-ink-subtle md:flex-row md:items-center">
          <span>© {year} {APP_NAME} — همهٔ حقوق محفوظ است.</span>
          <span>ساخته‌شده برای تیم‌های بازسازی سرزمین</span>
        </div>
      </div>
    </footer>
  );
}
