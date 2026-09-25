'use client';

import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/navigation';
import { SessionMenu } from './auth/SessionMenu';
import { LocaleSwitcher } from './LocaleSwitcher';

export function SiteNav({ locale }: { locale: string }) {
  const t = useTranslations();
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
          <Image
            src="/brand/platform-logo-transparent.png"
            alt={t('brand.logoAlt')}
            width={144}
            height={36}
            className="h-9 w-auto"
            priority
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

        <div className="flex shrink-0 items-center gap-3">
          <SessionMenu />
          <LocaleSwitcher current={locale} label={t('cover.languageLabel')} />
        </div>
      </div>
    </header>
  );
}
