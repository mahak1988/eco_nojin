'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { LocaleSwitcher } from '@/components/LocaleSwitcher';
import { SiteNav } from '@/components/SiteNav';
import { SiteFooter } from '@/components/SiteFooter';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';

interface PublicLayoutProps {
  children: ReactNode;
}

export function PublicLayout({ children }: PublicLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations('layout');
  const common = useTranslations('common');

  const isRtl = document.dir === 'rtl';

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-8">
            <Link
              href={`/${pathname.split('/')[1]}`}
              className="flex items-center gap-2 text-xl font-bold text-foreground"
            >
              <img src="/brand/platform-logo-transparent.png" alt="هیدروما نوژین" className="h-9 w-auto" />
            </Link>
            <nav className="hidden md:flex items-center gap-6" aria-label={t('mainNav')}>
              <SiteNav locale={pathname.split('/')[1]} />
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <LocaleSwitcher
              current={pathname.split('/')[1]}
              label="Language"
            />
            <Link
              href={`/${pathname.split('/')[1]}/market`}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Marketplace
            </Link>
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
      <footer className="border-t border-border bg-muted/30">
        <SiteFooter />
      </footer>
    </div>
  );
}

