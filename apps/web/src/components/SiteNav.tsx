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
    { href: '/help', label: t('help.title') },
  ];

  return (
    <header className="site-header" style={{ overflowX: 'clip' }}>
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-3 py-3 sm:gap-6 sm:px-5">
        <Link href="/home" aria-label={t('brand.name')} className="flex shrink-0 items-center">
          <Image
            src="/brand/platform-logo-transparent.png"
            alt={t('brand.logoAlt')}
            width={144}
            height={36}
            className="h-7 w-auto sm:h-9"
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

        <div className="flex shrink-0 items-center gap-1 sm:gap-3">
          <Link
            href="/help"
            aria-label={t('help.title')}
            className="inline-flex size-11 items-center justify-center rounded-full border border-[var(--line)] text-[var(--ink-soft)] hover:border-[var(--forest)] hover:text-[var(--forest)] md:hidden"
          >
            <span aria-hidden="true" className="text-base font-bold">
              ?
            </span>
          </Link>
          <SessionMenu />
          <LocaleSwitcher current={locale} label={t('cover.languageLabel')} />
        </div>
      </div>
    </header>
  );
}
