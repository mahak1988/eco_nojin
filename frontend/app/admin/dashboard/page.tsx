// frontend/app/admin/dashboard/page.tsx
'use client';

import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Users, Database, Activity, Settings } from 'lucide-react';

export default function AdminDashboardPage() {
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();

  // Example data, would come from API calls
  const stats = [
    { title: t('admin_stats_users'), value: '1,234', icon: Users },
    { title: t('admin_stats_data_points'), value: '56,789', icon: Database },
    { title: t('admin_stats_active_sessions'), value: '128', icon: Activity },
  ];

  if (!user || user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-[70vh]">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6 text-center text-red-700">
            {t('admin_access_denied')}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-6">{t('admin_dashboard_title')}</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {stats.map((stat, index) => (
          <Card key={index} style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link href="/admin/users">
          <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
            <Users className="h-8 w-8" />
            {t('admin_manage_users')}
          </Button>
        </Link>
        <Link href="/admin/data">
          <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
            <Database className="h-8 w-8" />
            {t('admin_manage_data')}
          </Button>
        </Link>
        <Link href="/admin/reports">
          <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
            <Activity className="h-8 w-8" />
            {t('admin_view_reports')}
          </Button>
        </Link>
        <Link href="/admin/settings">
          <Button variant="outline" className="w-full h-24 flex flex-col items-center justify-center gap-2">
            <Settings className="h-8 w-8" />
            {t('admin_system_settings')}
          </Button>
        </Link>
      </div>
    </div>
  );
}