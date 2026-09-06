import { Link, Outlet, useRouterState } from '@tanstack/react-router';
import { useTranslation } from 'react-i18next';
import { APP_NAME } from '@eco/config';
import { Badge, cn } from '@eco/ui';
import { useEffect, useRef, useState } from 'react';
import { BrandWordmark } from '../components/BrandMark';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from '../components/ThemeToggle';
import { UserMenu } from './UserMenu';

type NavPath =
  | '/'
  | '/carbon'
  | '/water'
  | '/soil'
  | '/climate'
  | '/satellite'
  | '/mrv'
  | '/models'
  | '/farms'
  | '/marketplace'
  | '/wallet'
  | '/ai-copilot'
  | '/chat'
  | '/aquacrop'
  | '/swat'
  | '/rothc'
  | '/erosion'
  | '/groundwater'
  | '/irrigation'
  | '/structures'
  | '/topography'
  | '/land-capability'
  | '/land-terrain'
  | '/land-drainage'
  | '/era5'
  | '/satellite-analyze'
  | '/blockchain'
  | '/carbon-oracle'
  | '/motors';

type NavItem = {
  to: NavPath;
  label: string;
  icon: string;
  group: 'overview' | 'scientific' | 'finance' | 'experimental';
};

const GROUPS: Record<NavItem['group'], { label: string; tone: 'brand' | 'sky' | 'leaf' | 'info' }> = {
  overview: { label: 'Overview', tone: 'brand' },
  scientific: { label: 'Scientific', tone: 'sky' },
  finance: { label: 'Finance', tone: 'leaf' },
  experimental: { label: 'Experimental', tone: 'info' },
};

const NAV: readonly NavItem[] = [
  { to: '/', label: 'Overview', icon: '📊', group: 'overview' },
  { to: '/carbon', label: 'Carbon', icon: '🌱', group: 'overview' },
  { to: '/water', label: 'Water', icon: '💧', group: 'overview' },
  { to: '/soil', label: 'Soil', icon: '🌍', group: 'overview' },
  { to: '/climate', label: 'Climate', icon: '🌤️', group: 'overview' },
  { to: '/satellite', label: 'Satellite', icon: '🛰️', group: 'overview' },
  { to: '/mrv', label: 'MRV', icon: '✅', group: 'overview' },
  { to: '/models', label: 'Models hub', icon: '🧠', group: 'overview' },
  { to: '/motors', label: 'Motors', icon: '⚙️', group: 'overview' },
  { to: '/farms', label: 'Farms', icon: '🚜', group: 'overview' },
  { to: '/aquacrop', label: 'AquaCrop', icon: '🌾', group: 'scientific' },
  { to: '/swat', label: 'SWAT+', icon: '🏞️', group: 'scientific' },
  { to: '/rothc', label: 'RothC', icon: '🪴', group: 'scientific' },
  { to: '/erosion', label: 'RUSLE', icon: '⛰️', group: 'scientific' },
  { to: '/groundwater', label: 'Groundwater', icon: '🌊', group: 'scientific' },
  { to: '/irrigation', label: 'Irrigation', icon: '💦', group: 'scientific' },
  { to: '/structures', label: 'Structures', icon: '🛠️', group: 'scientific' },
  { to: '/topography', label: 'Topography', icon: '🗻', group: 'scientific' },
  { to: '/land-capability', label: 'Land capability', icon: '🗺️', group: 'scientific' },
  { to: '/land-terrain', label: 'Land terrain', icon: '⛰️', group: 'scientific' },
  { to: '/land-drainage', label: 'Land drainage', icon: '🌊', group: 'scientific' },
  { to: '/era5', label: 'ERA5', icon: '🌡️', group: 'scientific' },
  { to: '/satellite-analyze', label: 'Sat analyze', icon: '🛰️', group: 'scientific' },
  { to: '/carbon-oracle', label: 'Carbon oracle', icon: '📜', group: 'finance' },
  { to: '/blockchain', label: 'Blockchain', icon: '⛓️', group: 'finance' },
  { to: '/marketplace', label: 'Marketplace', icon: '🛒', group: 'finance' },
  { to: '/wallet', label: 'Wallet', icon: '💰', group: 'finance' },
  { to: '/ai-copilot', label: 'AI Copilot', icon: '🤖', group: 'experimental' },
  { to: '/chat', label: 'Chat (WS)', icon: '💬', group: 'experimental' },
];

const TONE_ACCENT: Record<NavItem['group'], string> = {
  overview: 'bg-brand-500',
  scientific: 'bg-sky-500',
  finance: 'bg-leaf-500',
  experimental: 'bg-info',
};

export function WorkspaceLayout() {
  const { t } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);
  const [liveAnnouncement, setLiveAnnouncement] = useState('');
  const announcementTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { location } = useRouterState();
  const widthClass = collapsed ? 'md:w-16' : 'md:w-64';
  const shiftClass = collapsed ? 'md:ms-16' : 'md:ms-64';

  const announce = (message: string) => {
    if (announcementTimeoutRef.current) {
      clearTimeout(announcementTimeoutRef.current);
    }
    announcementTimeoutRef.current = setTimeout(() => {
      setLiveAnnouncement('');
      announcementTimeoutRef.current = setTimeout(() => {
        setLiveAnnouncement(message);
      }, 100);
    }, 3000);
  };

  useEffect(() => {
    return () => {
      if (announcementTimeoutRef.current) {
        clearTimeout(announcementTimeoutRef.current);
      }
    };
  }, []);

  const currentItem = NAV.find((n) => n.to === (location.pathname as NavPath));
  const currentGroup = currentItem?.group;

  return (
    <div className="min-h-screen bg-surface text-ink">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:start-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-raised"
      >
        پرش به محتوای اصلی
      </a>
      <aside
        aria-label="ناوبری اصلی"
        id="main-sidebar"
        className={cn(
          'fixed inset-y-0 start-0 z-20 hidden border-e border-ink/10 bg-surface-inverse text-ink-inverse transition-all duration-base ease-out-soft md:flex md:flex-col',
          widthClass,
        )}
      >
        {/* Brand */}
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-4">
          {!collapsed ? (
            <Link to="/" className="block">
              <div className="flex items-center gap-2.5 text-ink-inverse">
                <BrandWordmark size="sm" className="text-ink-inverse [&_span]:text-ink-inverse [&_span>span]:text-ink-inverse/70" />
              </div>
            </Link>
          ) : (
            <Link to="/" className="block">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-brand text-sm font-bold text-white">EN</span>
            </Link>
          )}
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            aria-label={collapsed ? 'باز کردن منوی کناری' : 'بستن منوی کناری'}
            aria-expanded={!collapsed}
            aria-controls="sidebar-nav"
            className="grid h-7 w-7 place-items-center rounded text-white/50 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
          >
            <span aria-hidden="true">{collapsed ? '→' : '←'}</span>
          </button>
        </div>

        {/* Nav */}
        <nav
          id="sidebar-nav"
          aria-label="ناوبری اصلی"
          className="flex-1 space-y-5 overflow-y-auto px-3 py-4 text-sm"
        >
          {(Object.keys(GROUPS) as NavItem['group'][]).map((g) => {
            const items = NAV.filter((i) => i.group === g);
            const accent = TONE_ACCENT[g];
            return (
              <div key={g} role="group" aria-labelledby={`nav-group-${g}`}>
                {!collapsed && (
                  <div
                    id={`nav-group-${g}`}
                    className="mb-1.5 flex items-center gap-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40"
                  >
                    <span className={cn('h-1.5 w-1.5 rounded-full', accent)} aria-hidden="true" />
                    {GROUPS[g].label}
                  </div>
                )}
                <ul className="space-y-0.5">
                  {items.map((item) => (
                    <li key={item.to}>
                      <Link
                        to={item.to}
                        className="group flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-white/80 transition hover:bg-white/8 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 [&.active]:bg-gradient-brand [&.active]:text-white [&.active]:shadow-soft"
                        activeOptions={{ exact: item.to === '/' }}
                        activeProps={{ className: 'active', 'aria-current': 'page' }}
                        title={item.label}
                      >
                        <span className="text-base" aria-hidden="true">{item.icon}</span>
                        {!collapsed && <span className="font-medium">{item.label}</span>}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="mt-auto border-t border-white/10 px-4 py-3 text-[10px] text-white/40">
          {!collapsed && (
            <div className="flex flex-col gap-1">
              <Badge tone="brand" variant="solid" className="w-fit">v2.0.0-beta</Badge>
              <span>{t('app.tagline')}</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main */}
      <div className={cn('transition-all duration-base ease-out-soft', shiftClass)}>
        {/* Top bar */}
        <header
          aria-label="هدر اصلی"
          className="sticky top-0 z-10 border-b border-ink/10 bg-surface/85 backdrop-blur-xl"
        >
          <div className="flex h-14 items-center gap-3 px-4 md:px-8">
            <nav aria-label="مسیر" className="flex items-center gap-2 text-sm">
              <span className="text-ink-muted">HyDroMa</span>
              {currentGroup && currentItem && (
                <>
                  <span aria-hidden="true" className="text-ink-subtle">/</span>
                  <span className="text-ink-muted">{GROUPS[currentGroup].label}</span>
                  <span aria-hidden="true" className="text-ink-subtle">/</span>
                  <span className="font-medium" aria-current="page">
                    {currentItem.icon} {currentItem.label}
                  </span>
                </>
              )}
            </nav>
            <div className="ms-auto flex items-center gap-2">
              <a
                href="/"
                target="_blank"
                rel="noopener noreferrer"
                className="hidden items-center gap-1.5 rounded-lg border border-ink/10 px-3 py-1.5 text-xs font-medium text-ink-muted transition-colors hover:bg-surface-muted hover:text-ink md:inline-flex"
              >
                ↗ <span>Public site</span>
              </a>
              <LanguageSwitcher />
              <ThemeToggle />
              <UserMenu />
            </div>
          </div>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          aria-label="محتوای اصلی"
          className={cn('px-4 py-6 md:px-8')}
        >
          <div
            aria-live="polite"
            aria-atomic="true"
            role="status"
            className="sr-only"
          >
            {liveAnnouncement}
          </div>
          <Outlet />
        </main>

        <footer className="mt-12 border-t border-ink/10 bg-surface-muted/40 px-4 py-6 text-xs text-ink-muted md:px-8">
          <div className="mx-auto flex max-w-content flex-col items-start justify-between gap-2 md:flex-row md:items-center">
            <span>
              © {new Date().getFullYear()} {APP_NAME} · HyDroMa Workspace
            </span>
            <span className="text-ink-subtle">Built for land restoration teams</span>
          </div>
        </footer>
      </div>
    </div>
  );
}