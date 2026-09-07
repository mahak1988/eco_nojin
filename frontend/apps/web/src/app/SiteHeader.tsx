import { useEffect, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { useTranslation } from 'react-i18next';
import { DASHBOARD_URL, APP_NAME } from '@eco/config';
import { cn } from '@eco/utils';
import { BrandWordmark } from '../components/BrandMark';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';

type NavLink = {
  href: '/' | '/knowledge' | '/models';
  labelKey: string;
  fallback: string;
};

const NAV: readonly NavLink[] = [
  { href: '/', labelKey: 'nav.home', fallback: 'Home' },
  { href: '/knowledge', labelKey: 'nav.knowledge', fallback: 'Knowledge' },
  { href: '/models', labelKey: 'nav.models', fallback: 'Models' },
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
        scrolled ? 'header-frost border-b border-ink/10' : 'bg-surface/0',
      )}
    >
      <div className="mx-auto flex h-header w-full max-w-content items-center justify-between gap-6 px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link to="/" className="flex items-center transition-opacity hover:opacity-80" aria-label={`${APP_NAME} home`}>
          <BrandWordmark size="sm" />
        </Link>

        {/* Desktop nav — small, quiet, Apple-style */}
        <nav aria-label={t('common.mainNav', 'منوی اصلی')} className="hidden items-center gap-7 md:flex">
          {NAV.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              className="text-xs font-normal text-ink-muted transition-colors hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              {t(link.labelKey, link.fallback)}
            </Link>
          ))}
          <a
            href={DASHBOARD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-normal text-ink-muted transition-colors hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            {t('nav.dashboard', 'HyDroMa')}
          </a>
        </nav>

        {/* Right side actions */}
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <LanguageSwitcher />
          <a
            href={DASHBOARD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden h-7 items-center rounded-full bg-gradient-brand px-3.5 text-xs font-medium text-white transition-all hover:opacity-90 focus-visible:outline-none sm:inline-flex"
            aria-label={t('home.openDashboard', 'Open HyDroMa')}
          >
            {t('home.openDashboard', 'ورود به HyDroMa')}
          </a>

          {/* Mobile menu toggle */}
          <button
            type="button"
            aria-label={t('common.openMenu', 'باز کردن منو')}
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((v) => !v)}
            className="inline-flex h-8 w-8 items-center justify-center rounded-full text-ink-muted hover:bg-surface-muted md:hidden"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
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
        <div className="header-frost border-t border-ink/10 md:hidden">
          <nav className="flex flex-col gap-1 p-5" aria-label={t('common.mainNav', 'منوی اصلی')}>
            {NAV.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-ink hover:bg-surface-muted"
              >
                {t(link.labelKey, link.fallback)}
              </Link>
            ))}
            <a
              href={DASHBOARD_URL}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMobileOpen(false)}
              className="mt-2 inline-flex items-center justify-center rounded-full bg-gradient-brand px-4 py-2.5 text-sm font-medium text-white"
            >
              {t('home.openDashboard', 'ورود به HyDroMa')}
            </a>
          </nav>
        </div>
      )}
    </header>
  );
}
