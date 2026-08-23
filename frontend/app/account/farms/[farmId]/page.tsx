// frontend/app/account/farms/[farmId]/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, MapPin, Ruler, Calendar, Users, Activity } from 'lucide-react';

interface FarmDetails {
  id: number;
  name: string;
  location: string;
  size_hectares: number;
  crop_type: string;
  planting_date: string;
  status: 'active' | 'inactive' | 'planned';
  farmer_id: number;
}

export default function FarmDetailPage() {
  const params = useParams();
  const { farmId } = params;
  const { user, token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [farm, setFarm] = useState<FarmDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFarm = async () => {
      try {
        // const res = await apiClient.get(`/api/v1/farms/${farmId}`);
        // setFarm(res.data);
        // Mock data for demonstration
        setFarm({
          id: parseInt(farmId as string),
          name: 'My Test Farm',
          location: 'Valley of Plenty, Region 5',
          size_hectares: 12.5,
          crop_type: 'Wheat',
          planting_date: '2023-09-15T00:00:00Z',
          status: 'active',
          farmer_id: user?.id || 1
        });
      } catch (err) {
        setError('Failed to load farm details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (farmId && token) {
      fetchFarm();
    }
  }, [farmId, token, user?.id]);

  if (!user) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            {t('common_please_log_in')}
          </CardContent>
        </Card>
      </div>
    );
  }

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
      <h1 className="text-3xl font-bold mb-6">{t('farm_detail_title', { name: farm?.name || farmId })}</h1>

      {loading || !farm ? (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle>{farm.name}</CardTitle>
                <Badge variant={farm.status === 'active' ? 'default' : farm.status === 'inactive' ? 'secondary' : 'outline'}>
                  {t(`farm_status_${farm.status}`)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center">
                  <MapPin className="h-4 w-4 text-muted-foreground mr-2" />
                  <span>{farm.location}</span>
                </div>
                <div className="flex items-center">
                  <Ruler className="h-4 w-4 text-muted-foreground mr-2" />
                  <span>{farm.size_hectares} ha</span>
                </div>
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 text-muted-foreground mr-2" />
                  <span>{new Date(farm.planting_date).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center">
                  <Activity className="h-4 w-4 text-muted-foreground mr-2" />
                  <span>{farm.crop_type}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle>{t('farm_actions')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button variant="outline" className="w-full">{t('farm_schedule_irrigation')}</Button>
                  <Button variant="outline" className="w-full">{t('farm_log_activity')}</Button>
                  <Button variant="outline" className="w-full">{t('farm_view_satellite')}</Button>
                </div>
              </CardContent>
            </Card>
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle>{t('farm_analytics')}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button variant="outline" className="w-full" asChild>
                    <a href={`/account/farms/${farm.id}/analytics`}>{t('farm_view_analytics')}</a>
                  </Button>
                  <Button variant="outline" className="w-full">{t('farm_predict_yield')}</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}