/** Dashboard shell: sidebar (categories + account) + nested routes.
 * All dashboard pages live under /dashboard/* — separated from public pages. */

import { NavLink, Link, Route, Routes } from 'react-router-dom';
import { Globe, LayoutDashboard, Settings, User } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { categories as registryCategories, registry } from '../../lib/hydromaregistry';
import { dashboardRoutes } from '../../routes/dashboardRoutes';

/** Dashboard shell with sidebar navigation and nested model routes. */
export default function DashboardLayout() {
  const { lang } = useLang();
  const isFa = lang === 'fa';

  const accountLinks = [
    { to: '/dashboard', label: isFa ? 'خانهٔ داشبورد' : 'Dashboard home', icon: LayoutDashboard, end: true },
    { to: '/dashboard/profile', label: isFa ? 'پروفایل' : 'Profile', icon: User, end: false },
    { to: '/dashboard/settings', label: isFa ? 'تنظیمات پلتفرم' : 'Settings', icon: Settings, end: false },
  ];

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 pt-8 sm:px-6 lg:flex-row">
      {/* sidebar */}
      <aside className="lg:w-72 lg:shrink-0">
        <div className="glass sticky top-20 flex flex-col gap-4 rounded-3xl p-5">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-extrabold text-emerald-50">
              {isFa ? 'داشبورد هیدروما' : 'HyDroMa dashboard'}
            </h2>
            <Link
              to="/"
              className="inline-flex items-center gap-1 text-[11px] font-bold text-leaf-300 hover:text-leaf-200"
            >
              <Globe className="h-3 w-3" aria-hidden />
              {isFa ? 'سایت عمومی' : 'Public site'}
            </Link>
          </div>

          {/* account */}
          <nav aria-label={isFa ? 'حساب' : 'Account'} className="flex flex-col gap-1">
            {accountLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-bold transition-colors ${
                    isActive ? 'bg-leaf-500/15 text-leaf-300' : 'text-emerald-100/60 hover:bg-white/5 hover:text-emerald-50'
                  }`
                }
              >
                <link.icon className="h-4 w-4" aria-hidden />
                {link.label}
              </NavLink>
            ))}
          </nav>

          {/* model categories */}
          <div className="flex flex-col gap-3 border-t border-white/8 pt-4">
            {registryCategories.map((category) => {
              const entries = registry.filter((entry) => entry.category === category.key);
              return (
                <div key={category.key}>
                  <p className="mb-1.5 px-1 text-[10px] font-extrabold tracking-wide text-emerald-100/40">
                    {isFa ? category.nameFa : category.nameEn} ({entries.length})
                  </p>
                  <div className="flex flex-col gap-0.5">
                    {entries.map((entry) => (
                      <NavLink
                        key={entry.id}
                        to={`/dashboard/models/${entry.id}`}
                        className={({ isActive }) =>
                          `rounded-lg px-2.5 py-1.5 text-[11px] transition-colors ${
                            isActive
                              ? 'bg-leaf-500/15 font-bold text-leaf-300'
                              : 'text-emerald-100/55 hover:bg-white/5 hover:text-emerald-50'
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
