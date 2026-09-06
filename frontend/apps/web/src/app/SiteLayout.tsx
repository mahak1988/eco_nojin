import { Outlet } from '@tanstack/react-router';
import { cn } from '@eco/utils';
import { Footer } from './Footer';
import { SiteHeader } from './SiteHeader';

export function SiteLayout() {
  return (
    <div className={cn('flex min-h-screen flex-col bg-surface text-ink')}>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:shadow-raised focus-visible:outline-none"
      >
        پرش به محتوای اصلی
      </a>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="flex-1 focus:outline-none">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}