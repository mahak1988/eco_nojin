/** Admin Layout — centralized navigation for all admin pages */

import { useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Shield, Users, Store, Activity, CreditCard, Settings, FileText, LayoutDashboard, ChevronLeft, ChevronRight } from 'lucide-react';
import { useBilingual } from '../../hooks/useBilingual';
import { useAuth } from '../../context/AuthContext';

interface AdminNavItem {
  path: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  badge?: number | string;
}

const ADMIN_NAV: AdminNavItem[] = [
  { path: '/dashboard/admin', label: 'نمای کلی', icon: LayoutDashboard, color: 'leaf' },
  { path: '/dashboard/admin/users', label: 'کاربران', icon: Users, color: 'aqua' },
  { path: '/dashboard/admin/vendors', label: 'فروشندگان', icon: Store, color: 'sand' },
  { path: '/dashboard/admin/marketplace', label: 'بازارگاه', icon: Activity, color: 'blue' },
  { path: '/dashboard/admin/transactions', label: 'تراکنش‌ها', icon: CreditCard, color: 'purple' },
  { path: '/dashboard/admin/reports', label: 'گزارش‌ها', icon: FileText, color: 'amber' },
  { path: '/dashboard/admin/settings', label: 'تنظیمات', icon: Settings, color: 'gray' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { fa } = useBilingual();
  const { user } = useAuth();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen bg-[var(--color-sand-50)] flex items-center justify-center p-8">
        <div className="glass rounded-2xl p-8 max-w-md text-center">
          <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-[var(--color-night-100)] mb-2">{fa('دسترسی محدود است', 'Access Denied')}</h1>
          <p className="text-[var(--color-night-200)]">{fa('فقط مدیران می‌توانند به این بخش دسترسی داشته باشند.', 'Only administrators can access this section.')}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-sand-50)]">
      {/* Top Bar */}
      <header className="glass sticky top-0 z-40 border-b border-white/10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="p-2 rounded-xl hover:bg-white/5 transition"
                aria-label={collapsed ? fa('باز کردن منو', 'Expand menu') : fa('بستن منو', 'Collapse menu')}
              >
                {collapsed ? <ChevronRight className="h-5 w-5 text-[var(--color-night-200)]" /> : <ChevronLeft className="h-5 w-5 text-[var(--color-night-200)]" />}
              </button>
              <Link to="/dashboard/admin" className="flex items-center gap-2 font-display text-lg font-semibold text-[var(--color-night-100)]">
                <Shield className="h-6 w-6 text-[var(--color-leaf-400)]" />
                <span className={collapsed ? 'hidden' : 'block'}>{fa('پنل ادمین', 'Admin Panel')}</span>
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-[var(--color-night-200)]/60 hidden sm:block">
                {fa('خوش آمدید', 'Welcome')} {user.full_name || user.email}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`fixed inset-y-0 left-0 z-30 transition-all duration-300 bg-[var(--color-night-50)] border-r border-white/10 ${collapsed ? 'w-16' : 'w-64'}`}
          aria-label={fa('منوی ادمین', 'Admin navigation')}
        >
          <nav className="flex flex-col h-full pt-4 px-2" aria-label={fa('پیمایش اصلی', 'Main navigation')}>
            <ul className="space-y-1 flex-1 overflow-y-auto" role="list">
              {ADMIN_NAV.map((item) => {
                const isActive = location.pathname === item.path || (item.path !== '/dashboard/admin' && location.pathname.startsWith(item.path + '/'));
                return (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                          isActive
                            ? `bg-[var(--color-${item.color}-500)]/15 text-[var(--color-${item.color}-400)]`
                            : 'text-[var(--color-night-200)]/70 hover:bg-white/5 hover:text-[var(--color-night-100)]'
                        } ${collapsed ? 'justify-center' : ''}`
                      }
                      title={collapsed ? fa(item.label, item.label) : undefined}
                    >
                      <item.icon className={`h-5 w-5 flex-shrink-0 ${isActive ? '' : ''}`} aria-hidden />
                      {!collapsed && <span className="font-medium">{fa(item.label, item.label)}</span>}
                      {item.badge && !collapsed && (
                        <span className="ml-auto px-2 py-0.5 text-[10px] font-bold rounded-full bg-[var(--color-leaf-500)]/20 text-[var(--color-leaf-400)]">
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
            <div className="pt-4 border-t border-white/10">
              <NavLink
                to="/dashboard"
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition text-[var(--color-night-200)]/70 hover:bg-white/5 hover:text-[var(--color-night-100)] ${collapsed ? 'justify-center' : ''}`}
                title={collapsed ? fa('بازگشت به داشبورد', 'Back to Dashboard') : undefined}
              >
                <LayoutDashboard className="h-5 w-5 flex-shrink-0" />
                {!collapsed && <span className="font-medium">{fa('داشبورد اصلی', 'Main Dashboard')}</span>}
              </NavLink>
            </div>
          </nav>
        </aside>

        {/* Main Content */}
        <main
          className={`flex-1 min-w-0 transition-all duration-300 ${collapsed ? 'ml-16' : 'ml-64'}`}
          style={{ marginLeft: collapsed ? '4rem' : '16rem' }}
        >
          <div className="p-6 sm:p-8">{children}</div>
        </main>
      </div>
    </div>
  );
}