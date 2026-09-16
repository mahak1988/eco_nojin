/** Admin Dashboard — system-wide administration overview */

import { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useBilingual } from '../../../hooks/useBilingual';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Users, Shield, BarChart3, Settings, Database, Globe, CreditCard, Package, TrendingUp, Loader2, AlertTriangle, Activity, Server, Lock, Bell, FileText } from 'lucide-react';

interface AdminStats {
  total_users: number;
  total_orders: number;
  total_revenue: number;
  active_vendors: number;
  pending_approvals: number;
  system_health: 'healthy' | 'degraded' | 'critical';
  db_size: string;
  api_latency: number;
}

interface RecentActivity {
  id: string;
  type: 'user_registered' | 'order_placed' | 'payment_received' | 'vendor_approved' | 'product_approved' | 'system_alert';
  description: string;
  timestamp: string;
  user_id?: string;
}

export default function AdminDashboard() {
  const { fa } = useBilingual();
  const { user, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
        const token = localStorage.getItem('hydroma_token');
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const [statsRes, activitiesRes] = await Promise.all([
          fetch(`${apiBase}/api/v1/admin/stats`, { headers }).catch(() => null),
          fetch(`${apiBase}/api/v1/admin/activities?limit=20`, { headers }).catch(() => null),
        ]);

        if (statsRes?.ok) setStats(await statsRes.json());
        if (activitiesRes?.ok) setActivities((await activitiesRes.json()).activities || []);
      } catch {
        // Ignore errors, use mock data
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) loadData();
  }, [authLoading]);

  if (authLoading || loading) {
    return (
      <>
        <Seo title={fa('پنل ادمین', 'Admin Dashboard')} path="/dashboard/admin" />
        <div className="min-h-screen bg-[var(--color-sand-50)] flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--color-leaf-400)]" aria-hidden />
        </div>
      </>
    );
  }

  const { user } = useAuth();
  if (!user?.is_admin) {
    return (
      <>
        <Seo title={fa('پنل ادمین', 'Admin Dashboard')} path="/dashboard/admin" />
        <div className="min-h-screen bg-[var(--color-sand-50)] flex items-center justify-center">
          <Reveal className="text-center p-8">
            <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" aria-hidden />
            <h1 className="text-2xl font-bold text-[var(--color-night-100)] mb-2">{fa('دسترسی محدود است', 'Access Denied')}</h1>
            <p className="text-[var(--color-night-200)]">{fa('فقط مدیران می‌توانند به این صفحه دسترسی داشته باشند.', 'Only administrators can access this page.')}</p>
          </Reveal>
        </div>
      </>
    );
  }

  const statCards = [
    { icon: Users, label: fa('کل کاربران', 'Total Users'), value: stats?.total_users?.toLocaleString() ?? '—', color: 'leaf' },
    { icon: Package, label: fa('کل سفارشات', 'Total Orders'), value: stats?.total_orders?.toLocaleString() ?? '—', color: 'aqua' },
    { icon: CreditCard, label: fa('کل درآمد', 'Total Revenue'), value: stats?.total_revenue ? `${stats.total_revenue.toLocaleString()} IRR` : '—', color: 'sand' },
    { icon: Shield, label: fa('فروشندگان فعال', 'Active Vendors'), value: stats?.active_vendors?.toLocaleString() ?? '—', color: 'leaf' },
    { icon: Activity, label: fa('منتظر تأیید', 'Pending Approvals'), value: stats?.pending_approvals?.toLocaleString() ?? '—', color: 'amber' },
    { icon: Database, label: fa('حجم دیتابیس', 'DB Size'), value: stats?.db_size ?? '—', color: 'blue' },
  ];

  const quickActions = [
    { path: '/dashboard/admin/users', icon: Users, label: fa('مدیریت کاربران', 'Manage Users'), color: 'leaf' },
    { path: '/dashboard/admin/vendors', icon: Shield, label: fa('تأیید فروشندگان', 'Approve Vendors'), color: 'aqua' },
    { path: '/dashboard/admin/marketplace', icon: Package, label: fa('مدیریت بازارگاه', 'Marketplace Management'), color: 'sand' },
    { path: '/dashboard/admin/transactions', icon: TrendingUp, label: fa('تراکنش‌ها', 'Transactions'), color: 'blue' },
    { path: '/dashboard/admin/settings', icon: Settings, label: fa('تنظیمات سیستم', 'System Settings'), color: 'gray' },
    { path: '/dashboard/admin/reports', icon: FileText, label: fa('گزارش‌ها', 'Reports'), color: 'purple' },
  ];

  const systemHealthColor = stats?.system_health === 'healthy' ? 'text-[var(--color-leaf-400)]' : stats?.system_health === 'degraded' ? 'text-[#e8c66b]' : 'text-red-400';
  const systemHealthLabel = stats?.system_health === 'healthy' ? fa('سالم', 'Healthy') : stats?.system_health === 'degraded' ? fa('تنهاده', 'Degraded') : fa('بحرانی', 'Critical');

  return (
    <>
      <Seo title={fa('پنل ادمین', 'Admin Dashboard')} path="/dashboard/admin" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Shield className="h-6 w-6 text-[var(--color-leaf-400)]" />
                  {fa('پنل ادمین', 'Admin Dashboard')}
                </h1>
                <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{fa('نمای کلی سیستم و مدیریت', 'System overview and management')}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${systemHealthColor} bg-opacity-20`}>
                  <Activity className="h-3 w-3 inline-block ml-1" /> {systemHealthLabel}
                </span>
              </div>
            </div>
          </Reveal>

          {/* Stats Grid */}
          <Reveal delay={0.1}>
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
              {statCards.map((stat, index) => (
                <div key={stat.label} className="glass rounded-2xl p-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-xl bg-[var(--color-${stat.color}-500)]/15`}>
                      <stat.icon className={`w-6 h-6 text-[var(--color-${stat.color}-400)]`} aria-hidden />
                    </div>
                    <div>
                      <p className="text-xs text-[var(--color-night-200)]/60">{stat.label}</p>
                      <p className="text-xl font-extrabold text-[var(--color-night-100)]">{stat.value}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>

          {/* Quick Actions + Recent Activity */}
          <Reveal delay={0.2}>
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Quick Actions */}
              <div className="lg:col-span-1">
                <h3 className="mb-4 text-lg font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Activity className="h-5 w-5 text-[var(--color-leaf-400)]" />
                  {fa('اقدامات سریع', 'Quick Actions')}
                </h3>
                <div className="glass rounded-2xl p-4 space-y-3">
                  {quickActions.map((action, index) => (
                    <a key={action.label} href={action.path} className="glass-hover rounded-xl p-4 flex items-center gap-3 block transition-all">
                      <div className={`p-3 rounded-xl bg-[var(--color-${action.color}-500)]/15`}>
                        <action.icon className={`w-5 h-5 text-[var(--color-${action.color}-400)]`} aria-hidden />
                      </div>
                      <span className="text-sm font-medium text-[var(--color-night-100)]">{action.label}</span>
                    </a>
                  ))}
                </div>
              </div>

              {/* Recent Activity + System Info */}
              <div className="lg:col-span-2 space-y-6">
                {/* Recent Activity */}
                <div className="glass rounded-2xl p-6">
                  <h3 className="mb-4 text-lg font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                    <Activity className="h-5 w-5 text-[var(--color-leaf-400)]" />
                    {fa('فعالیت‌های اخیر', 'Recent Activity')}
                  </h3>
                  {activities.length === 0 ? (
                    <p className="text-sm text-[var(--color-night-200)]/60 text-center py-4">{fa('فعالیتی یافت نشد', 'No recent activity')}</p>
                  ) : (
                    <div className="space-y-3">
                      {activities.slice(0, 10).map((activity) => (
                        <div key={activity.id} className="flex items-center gap-3 p-3 rounded-xl bg-[var(--color-night-50)]">
                          <div className="p-2 rounded-lg bg-[var(--color-leaf-500)]/15">
                            <Activity className="h-4 w-4 text-[var(--color-leaf-400)]" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-[var(--color-night-100)] truncate">{activity.description}</p>
                            <p className="text-xs text-[var(--color-night-200)]/60">{new Date(activity.timestamp).toLocaleString()}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* System Info */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="glass rounded-2xl p-4 text-center">
                    <Server className="h-8 w-8 text-[var(--color-aqua-400)] mx-auto mb-2" />
                    <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{fa === 'fa' ? 'آنلاین' : 'Online'}</p>
                    <p className="text-xs text-[var(--color-night-200)]/60">{fa('وضعیت سرور', 'Server Status')}</p>
                  </div>
                  <div className="glass rounded-2xl p-4 text-center">
                    <Database className="h-8 w-8 text-[var(--color-leaf-400)] mx-auto mb-2" />
                    <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{stats?.db_size ?? '—'}</p>
                    <p className="text-xs text-[var(--color-night-200)]/60">{fa('حجم دیتابیس', 'DB Size')}</p>
                  </div>
                  <div className="glass rounded-2xl p-4 text-center">
                    <Lock className="h-8 w-8 text-purple-400 mx-auto mb-2" />
                    <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{fa === 'fa' ? 'فعال' : 'Enabled'}</p>
                    <p className="text-xs text-[var(--color-night-200)]/60">{fa('SSL/HTTPS', 'SSL/HTTPS')}</p>
                  </div>
                  <div className="glass rounded-2xl p-4 text-center">
                    <Bell className="h-8 w-8 text-[var(--color-leaf-400)] mx-auto mb-2" />
                    <p className="text-2xl font-extrabold text-[var(--color-night-100)]">{stats?.pending_approvals ?? 0}</p>
                    <p className="text-xs text-[var(--color-night-200)]/60">{fa('اعلان‌ها', 'Notifications')}</p>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </>
  );
}