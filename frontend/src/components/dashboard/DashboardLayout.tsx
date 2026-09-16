/** Dashboard shell: full-width layout with a horizontal top navigation
 * (sidebar removed). Account actions live in the top bar; live pages and
 * model categories sit in a horizontal, scrollable strip below. Model pages
 * are reachable from the dashboard home registry. */

import { NavLink, Link, Route, Routes } from 'react-router-dom';
import { Globe, LayoutDashboard, LogIn, Settings, User, Store, Shield, CreditCard, Truck, HandCoins, Users, Database, Activity, SlidersHorizontal } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { categories as registryCategories } from '../../lib/hydromaregistry';
import { dashboardRoutes } from '../../routes/dashboardRoutes';

/** Full-width dashboard shell with horizontal navigation (no sidebar). */
export default function DashboardLayout() {
  const { lang } = useLang();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const isFa = lang === 'fa';

  const accountLinks = [
    { to: '/dashboard', label: isFa ? 'داشبورد' : 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/dashboard/profile', label: isFa ? 'پروفایل' : 'Profile', icon: User, end: false },
    { to: '/dashboard/settings', label: isFa ? 'تنظیمات' : 'Settings', icon: Settings, end: false },
    { to: '/dashboard/login', label: isFa ? 'ورود' : 'Login', icon: LogIn, end: false },
  ];

  const commerceLinks = [
    { to: '/dashboard/commerce', label: isFa ? 'مدیریت تجارت' : 'Commerce', icon: Store },
    { to: '/dashboard/commerce/orders', label: isFa ? 'سفارش‌ها' : 'Orders', icon: CreditCard },
    { to: '/dashboard/commerce/payments', label: isFa ? 'پرداخت‌ها' : 'Payments', icon: HandCoins },
    { to: '/dashboard/commerce/shipping', label: isFa ? 'ارسال' : 'Shipping', icon: Truck },
    { to: '/dashboard/commerce/settlements', label: isFa ? 'تسویه' : 'Settlements', icon: Database },
  ];

  const adminLinks = [
    { to: '/dashboard/admin', label: isFa ? 'پنل ادمین' : 'Admin Panel', icon: Shield },
    { to: '/dashboard/admin/users', label: isFa ? 'کاربران' : 'Users', icon: Users },
    { to: '/dashboard/admin/vendors', label: isFa ? 'فروشندگان' : 'Vendors', icon: Store },
    { to: '/dashboard/admin/marketplace', label: isFa ? 'بازارگاه' : 'Marketplace', icon: Activity },
    { to: '/dashboard/admin/transactions', label: isFa ? 'تراکنش‌ها' : 'Transactions', icon: CreditCard },
    { to: '/dashboard/admin/settings', label: isFa ? 'تنظیمات سیستم' : 'System Settings', icon: SlidersHorizontal },
  ];

  const liveLinks = [
    { to: '/dashboard/live/status', label: isFa ? 'وضعیت سرویس' : 'Status' },
    { to: '/dashboard/live/indices', label: isFa ? 'مدل‌های علمی (زنده)' : 'Models (live)' },
    { to: '/dashboard/monitoring', label: isFa ? 'پایش مزرعه' : 'Monitoring' },
    { to: '/dashboard/live/satellite', label: isFa ? 'ماهواره' : 'Satellite' },
    { to: '/dashboard/live/chain', label: isFa ? 'زنجیره علمی' : 'Scientific chain' },
    { to: '/dashboard/science-live', label: isFa ? 'علم زنده' : 'Science live' },
    { to: '/dashboard/economy', label: isFa ? 'اقتصاد (NPV/ROI)' : 'Economy' },
    { to: '/dashboard/validation', label: isFa ? 'راستی‌آزمایی' : 'Verification' },
    { to: '/dashboard/support', label: isFa ? 'پشتیبانی' : 'Support' },
    { to: '/dashboard/advisory', label: isFa ? 'مشاوره' : 'Advisory' },
  ];

  return (
    <div className="mx-auto w-full max-w-7xl px-4 pt-6 sm:px-6">
      {/* horizontal top navigation (replaces the sidebar) */}
      <header className="glass sticky top-20 z-30 rounded-2xl px-4 py-3">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
          <Link
            to="/dashboard"
            className="font-display flex items-center gap-2 text-lg font-semibold text-ink-1"
          >
            <img src="/logo-econojin.png" alt="" loading="eager" width={26} height={26} className="shrink-0 rounded-lg object-cover" aria-hidden />
            {isFa ? 'داشبورد هیدروما' : 'HyDroMa dashboard'}
          </Link>
          <Link
            to="/"
            className="inline-flex items-center gap-1 text-[11px] font-bold text-leaf-300 hover:text-leaf-200"
          >
            <Globe className="h-3 w-3" aria-hidden />
            {isFa ? 'سایت عمومی' : 'Public site'}
          </Link>

          {/* account actions */}
          <nav
            aria-label={isFa ? 'حساب کاربری' : 'Account'}
            className="ms-auto flex flex-wrap items-center gap-1.5"
          >
            {accountLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  `inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-bold transition-colors ${
                    isActive
                      ? 'bg-leaf-500/15 text-leaf-300'
                      : 'text-emerald-100/60 hover:bg-white/5 hover:text-emerald-50'
                  }`
                }
              >
                <link.icon className="h-3.5 w-3.5" aria-hidden />
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* live pages + model categories (horizontal, scrollable) */}
        <nav
          aria-label={isFa ? 'پیمایش داشبورد' : 'Dashboard navigation'}
          className="mt-3 flex items-center gap-1.5 overflow-x-auto pb-1"
        >
          {liveLinks.filter((link) => isAdmin || link.to !== '/dashboard/live/status').map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `shrink-0 rounded-full px-3 py-1.5 text-[11px] font-bold transition-colors ${
                  isActive
                    ? 'bg-aqua-500/15 text-aqua-300'
                    : 'text-ink-3 hover:bg-white/5 hover:text-ink-1'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}

          {commerceLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `shrink-0 rounded-full px-3 py-1.5 text-[11px] font-bold transition-colors ${
                  isActive
                    ? 'bg-leaf-500/15 text-leaf-300'
                    : 'text-ink-3 hover:bg-white/5 hover:text-ink-1'
                }`
              }
            >
              <link.icon className="h-3.5 w-3.5 mr-1" aria-hidden />
              {link.label}
            </NavLink>
          ))}

          {isAdmin && adminLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `shrink-0 rounded-full px-3 py-1.5 text-[11px] font-bold transition-colors ${
                  isActive
                    ? 'bg-purple-500/15 text-purple-300'
                    : 'text-ink-3 hover:bg-white/5 hover:text-ink-1'
                }`
              }
            >
              <link.icon className="h-3.5 w-3.5 mr-1" aria-hidden />
              {link.label}
            </NavLink>
          ))}

          <span className="mx-1 h-4 w-px shrink-0 bg-white/10" aria-hidden />

          {registryCategories.map((category) => (
            <Link
              key={category.key}
                            to={`/dashboard/category/${category.key}`}
              className="shrink-0 rounded-full px-3 py-1.5 text-[11px] font-bold text-ink-3 transition-colors hover:bg-white/5 hover:text-ink-1"
            >
              {isFa ? category.nameFa : category.nameEn}
            </Link>
          ))}
        </nav>
      </header>

      {/* content */}
      <main className="min-w-0 flex-1 pb-10 pt-6">
        <Routes>
          {dashboardRoutes.map((route) => (
            <Route key={route.path} path={route.path} element={route.element} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
