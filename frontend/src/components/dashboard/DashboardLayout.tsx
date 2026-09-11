/** Dashboard shell: sidebar (categories + account) + nested routes.
 * All dashboard pages live under /dashboard/* — separated from public pages. */

import { useState } from 'react';
import { NavLink, Link, Route, Routes } from 'react-router-dom';
import { Globe, LayoutDashboard, Settings, User, Menu, X } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { categories as registryCategories, registry } from '../../lib/hydromaregistry';
import { dashboardRoutes } from '../../routes/dashboardRoutes';

/** Dashboard shell with collapsible sidebar navigation and nested model routes. */
export default function DashboardLayout() {
  const { lang } = useLang();
  const isFa = lang === 'fa';
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const accountLinks = [
    { to: '/dashboard', label: isFa ? 'خانهٔ داشبورد' : 'Dashboard home', icon: LayoutDashboard, end: true },
    { to: '/dashboard/profile', label: isFa ? 'پروفایل' : 'Profile', icon: User, end: false },
    { to: '/dashboard/settings', label: isFa ? 'تنظیمات پلتفرم' : 'Settings', icon: Settings, end: false },
  ];

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 pt-8 sm:px-6 lg:flex-row">
      {/* sidebar — collapsible on desktop, off-canvas drawer on mobile */}
      <aside
        className={`
          lg:shrink-0 transition-all duration-300
          ${sidebarOpen ? 'fixed inset-0 z-40 lg:relative lg:translate-x-0' : 'fixed inset-y-0 start-0 z-40 -translate-x-full lg:translate-x-0 lg:static lg:w-72 lg:block'}
        `}
      >
        <div className="glass h-full overflow-y-auto rounded-3xl p-5 lg:sticky lg:top-20">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-extrabold text-[var(--color-night-100)]">
              {isFa ? 'داشبورد هیدروما' : 'HyDroMa dashboard'}
            </h2>
            <div className="flex items-center gap-2">
              <Link
                to="/"
                className="inline-flex items-center gap-1 text-[11px] font-bold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)]"
              >
                <Globe className="h-3 w-3" aria-hidden />
                {isFa ? 'سایت عمومی' : 'Public site'}
              </Link>
              <button
                type="button"
                onClick={() => setSidebarOpen(false)}
                className="lg:hidden rounded-xl p-1 text-[var(--color-night-200)]/50 hover:text-[var(--color-night-100)]"
                aria-label={isFa ? 'بستن منو' : 'Close menu'}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* account */}
          <nav aria-label={isFa ? 'حساب' : 'Account'} className="mt-4 flex flex-col gap-1">
            {accountLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-bold transition-colors ${
                    isActive ? 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-300)]' : 'text-[var(--color-night-200)]/60 hover:bg-white/5 hover:text-[var(--color-night-100)]'
                  }`
                }
              >
                <link.icon className="h-4 w-4" aria-hidden />
                {link.label}
              </NavLink>
            ))}
          </nav>

          {/* model categories */}
          <div className="mt-4 flex flex-col gap-4 border-t border-white/8 pt-4">
            {registryCategories.map((category) => {
              const entries = registry.filter((entry) => entry.category === category.key);
              if (entries.length === 0) return null;
              return (
                <div key={category.key}>
                  <p className="mb-1.5 px-1 text-[10px] font-extrabold tracking-wide text-[var(--color-night-200)]/40">
                    {isFa ? category.nameFa : category.nameEn} ({entries.length})
                  </p>
                  <div className="flex flex-col gap-0.5">
                    {entries.map((entry) => (
                      <NavLink
                        key={entry.id}
                        to={`/dashboard/models/${entry.id}`}
                        onClick={() => setSidebarOpen(false)}
                        className={({ isActive }) =>
                          `rounded-lg px-2.5 py-1.5 text-[11px] transition-colors ${
                            isActive
                              ? 'bg-[var(--color-leaf-500)]/15 font-bold text-[var(--color-leaf-300)]'
                              : 'text-[var(--color-night-200)]/55 hover:bg-white/5 hover:text-[var(--color-night-100)]'
                          }`
                        }
                        dir="ltr"
                      >
                        {entry.id}
                      </NavLink>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </aside>

      {/* mobile menu toggle */}
      <button
        type="button"
        onClick={() => setSidebarOpen(true)}
        className="lg:hidden fixed bottom-6 end-6 z-30 rounded-full bg-[var(--color-leaf-500)]/20 p-3 text-[var(--color-leaf-300)] backdrop-blur"
        aria-label={isFa ? 'باز کردن منو' : 'Open menu'}
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* content */}
      <main className="min-w-0 flex-1 pb-10">
        <Routes>
          {dashboardRoutes.map((route) => (
            <Route key={route.path} path={route.path} element={route.element} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
