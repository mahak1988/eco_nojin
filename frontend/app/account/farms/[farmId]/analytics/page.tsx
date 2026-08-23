// frontend/app/account/farms/[farmId]/analytics/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Activity, Droplets, Sun, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface FarmAnalyticsData {
  id: number;
  farm_id: number;
  date: string;
  soil_moisture: number;
  temperature_avg: number;
  growth_index: number;
}

export default function FarmAnalyticsPage() {
  const params = useParams();
  const { farmId } = params;
  const { token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [analyticsData, setAnalyticsData] = useState<FarmAnalyticsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        // const res = await apiClient.get(`/api/v1/farms/${farmId}/analytics`);
        // setAnalyticsData(res.data);
        // Mock data for demonstration
        setAnalyticsData([
          { id: 1, farm_id: parseInt(farmId as string), date: '2023-10-20', soil_moisture: 45, temperature_avg: 22, growth_index: 0.65 },
          { id: 2, farm_id: parseInt(farmId as string), date: '2023-10-21', soil_moisture: 42, temperature_avg: 23, growth_index: 0.67 },
          { id: 3, farm_id: parseInt(farmId as string), date: '2023-10-22', soil_moisture: 48, temperature_avg: 21, growth_index: 0.68 },
          { id: 4, farm_id: parseInt(farmId as string), date: '2023-10-23', soil_moisture: 50, temperature_avg: 20, growth_index: 0.70 },
          { id: 5, farm_id: parseInt(farmId as string), date: '2023-10-24', soil_moisture: 47, temperature_avg: 22, growth_index: 0.72 },
          { id: 6, farm_id: parseInt(farmId as string), date: '2023-10-25', soil_moisture: 44, temperature_avg: 23, growth_index: 0.74 },
          { id: 7, farm_id: parseInt(farmId as string), date: '2023-10-26', soil_moisture: 46, temperature_avg: 22, growth_index: 0.76 },
        ]);
      } catch (err) {
        setError('Failed to load analytics data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (farmId && token) {
      fetchAnalytics();
    }
  }, [farmId, token]);

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6 text-center text-red-700 flex items-center justify-center">
            <AlertCircle className="h-5 w-5 mr-2" />
            {error}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <h1 className="text-3xl font-bold mb-6">{t('farm_analytics_title', { farmId })}</h1>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <>
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                {t('farm_growth_index_trend')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={analyticsData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                  <XAxis dataKey="date" stroke={colors.textMuted} />
                  <YAxis stroke={colors.textMuted} />
                  <Tooltip wrapperStyle={{ backgroundColor: colors.cardBg, borderColor: colors.border }} />
                  <Area type="monotone" dataKey="growth_index" stroke={colors.primary} fill={`${colors.primary}20`} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Droplets className="h-5 w-5" />
                  {t('farm_soil_moisture')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={analyticsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                    <XAxis dataKey="date" stroke={colors.textMuted} />
                    <YAxis stroke={colors.textMuted} domain={[30, 60]} />
                    <Tooltip wrapperStyle={{ backgroundColor: colors.cardBg, borderColor: colors.border }} />
                    <Line type="monotone" dataKey="soil_moisture" stroke={colors.accent} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sun className="h-5 w-5" />
                  {t('farm_temperature')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={analyticsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.border} />
                    <XAxis dataKey="date" stroke={colors.textMuted} />
                    <YAxis stroke={colors.textMuted} />
                    <Tooltip wrapperStyle={{ backgroundColor: colors.cardBg, borderColor: colors.border }} />
                    <Line type="monotone" dataKey="temperature_avg" stroke={colors.warning || '#f59e0b'} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}