import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { APP_NAME } from '@eco/config';
import { cn } from '@eco/utils';
import { BrandWordmark } from '../components/BrandMark';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

type NavLink = {
  href: string;
  labelKey: string;
  fallback: string;
  external?: boolean;
};

const NAV: readonly NavLink[] = [
  { href: '/', labelKey: 'nav.home', fallback: 'Home' },
  { href: '/knowledge', labelKey: 'nav.knowledge', fallback: 'Knowledge' },
  { href: '/models', labelKey: 'nav.models', fallback: 'Models' },
  {
    href: '/dashboard',
    labelKey: 'nav.dashboard',
    fallback: 'HyDroMa',
    external: true,
  },
];

export function SiteHeader() {
  const { t } = useTranslation();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={cn(
        'sticky top-0 z-40 w-full transition-all duration-base ease-out-soft',
        scrolled
          ? 'border-b border-ink/10 bg-surface/85 backdrop-blur-xl shadow-soft'
          : 'bg-surface/0',
      )}
    >
      <div className="mx-auto flex h-header w-full max-w-content items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <a
          href="/"
          className="flex items-center gap-3 transition-opacity hover:opacity-80"
          aria-label={`${APP_NAME} home`}
        >
          <BrandWordmark size="md" />
        </a>

        {/* Desktop nav */}
        <nav aria-label="ناوبری اصلی" className="hidden items-center gap-1 md:flex">
          {NAV.map((link) =>
            link.external ? (
              <a
                key={link.href}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              >
                {t(link.labelKey, link.fallback)}
                <span aria-hidden="true" className="ms-1 text-[10px]">↗</span>
              </a>
            ) : (
              <a
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
              >
                {t(link.labelKey, link.fallback)}
              </a>
            ),
          )}
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <LanguageSwitcher />
<a
            href="/dashboard"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-1.5 rounded-lg bg-gradient-brand px-4 py-2 text-sm font-semibold text-white shadow-soft transition-all hover:shadow-raised focus-visible:shadow-glow focus-visible:outline-none sm:inline-flex"
            aria-label={`${t('home.openDashboard', 'Open HyDroMa')} — opens in a new tab`}
          >
            {t('nav.dashboard', 'HyDroMa')}
            <span aria-hidden="true">→</span>
          </a>

          {/* Mobile menu toggle */}
          <button
            type="button"
            aria-label="Open menu"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-ink/10 text-ink-muted hover:bg-surface-muted md:hidden"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileOpen ? (
                <path d="M6 6l12 12M18 6l-12 12" strokeLinecap="round" />
              ) : (
                <>
                  <path d="M4 7h16" strokeLinecap="round" />
                  <path d="M4 12h16" strokeLinecap="round" />
                  <path d="M4 17h16" strokeLinecap="round" />
                </>
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu drawer */}
      {mobileOpen && (
        <div className="border-t border-ink/10 bg-surface/95 backdrop-blur-xl md:hidden">
          <nav className="flex flex-col gap-1 p-4">
            {NAV.map((link) => (
              <a
                key={link.href}
                href={link.href}
                target={link.external ? '_blank' : undefined}
                rel={link.external ? 'noopener noreferrer' : undefined}
                onClick={() => setMobileOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-ink hover:bg-surface-muted"
              >
                {t(link.labelKey, link.fallback)}
              </a>
            ))}
            <a
              href="/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMobileOpen(false)}
              className="mt-2 inline-flex items-center justify-center gap-1.5 rounded-lg bg-gradient-brand px-4 py-2.5 text-sm font-semibold text-white"
            >
              {t('home.openDashboard', 'Open HyDroMa')}
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}