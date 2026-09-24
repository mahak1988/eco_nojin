import { getTranslations } from 'next-intl/server';
import { Link } from '@/i18n/navigation';
import { LocaleSwitcher } from './LocaleSwitcher';

export async function SiteNav({ locale }: { locale: string }) {
  const t = await getTranslations();
  const items = [
    { href: '/home', label: t('nav.home') },
    { href: '/hydroma', label: t('nav.science') },
    { href: '/market', label: t('nav.market') },
    { href: '/status', label: t('nav.status') },
  ];

  return (
    <header className="site-header">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-5 py-3">
        <Link href="/home" aria-label={t('brand.name')} className="flex shrink-0 items-center">
          <img
            src="/brand/platform-logo-transparent.png"
            alt={t('brand.logoAlt')}
            className="h-9 w-auto"
          />
        </Link>

        <nav className="hidden items-center gap-6 text-sm md:flex">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-[var(--ink-soft)] transition-colors hover:text-[var(--ink)]"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <LocaleSwitcher current={locale} label={t('cover.languageLabel')} />
      </div>
    </header>
  );
}
