import { getTranslations } from 'next-intl/server';
import { Link } from '@/i18n/navigation';

const YEAR = new Date().getFullYear();

const PUBLIC_LINKS = [
  { href: '/about', key: 'nav.about' },
  { href: '/statements', key: 'statements.title' },
  { href: '/platform', key: 'platformOverview.title' },
  { href: '/services', key: 'services.title' },
  { href: '/evidence', key: 'evidence.title' },
  { href: '/learn', key: 'learn.title' },
  { href: '/ai', key: 'ai.title' },
  { href: '/trust', key: 'trust.title' },
  { href: '/developers', key: 'developers.title' },
  { href: '/legal', key: 'legal.title' },
  { href: '/accessibility', key: 'accessibility.title' },
] as const;

export async function SiteFooter() {
  const t = await getTranslations();
  return (
    <footer className="mt-auto border-t border-line">
      <nav
        aria-label={t('footer.navTitle')}
        className="mx-auto flex max-w-6xl flex-wrap gap-x-4 gap-y-2 px-6 pt-6 text-xs"
      >
        {PUBLIC_LINKS.map((item) => (
          <Link key={item.href} href={item.href} className="text-ink-soft hover:text-ink">
            {t(item.key)}
          </Link>
        ))}
      </nav>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-6 py-6 text-xs text-ink-faint">
        <span>
          © {YEAR} · {t('brand.name')}
        </span>
        <div className="flex items-center gap-4">
          <Link href="/status" className="hover:text-ink">
            {t('nav.status')}
          </Link>
          <a href="/sitemap.xml" className="hover:text-ink">
            {t('footer.sitemap')}
          </a>
          <span className="chip">{t('footer.techStack')}</span>
        </div>
      </div>
    </footer>
  );
}
