// frontend/app/science/satellite/[taskId]/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Image } from 'lucide-react';

interface SatelliteAnalysisResult {
  id: number;
  task_id: string;
  date_processed: string;
  area_covered_hectares: number;
  ndvi_mean: number;
  ndvi_std: number;
  image_url: string;
  anomaly_detected: boolean;
  anomaly_description?: string;
}

export default function SatelliteAnalysisPage() {
  const params = useParams();
  const { taskId } = params;
  const { token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [analysis, setAnalysis] = useState<SatelliteAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        // const res = await apiClient.get(`/api/v1/satellite/analysis/${taskId}`);
        // setAnalysis(res.data);
        // Mock data for demonstration
        setAnalysis({
          id: parseInt(taskId as string),
          task_id: 'SAT-TASK-2023-001',
          date_processed: '2023-10-28T12:00:00Z',
          area_covered_hectares: 125.5,
          ndvi_mean: 0.65,
          ndvi_std: 0.12,
          image_url: '/placeholder-satellite-image.jpg', // Placeholder
          anomaly_detected: true,
          anomaly_description: 'Potential water stress detected in the north-east quadrant.'
        });
      } catch (err) {
        setError('Failed to load satellite analysis data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (taskId) {
      fetchAnalysis();
    }
  }, [taskId, token]);

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
      <h1 className="text-3xl font-bold mb-6">{t('satellite_analysis_title', { id: taskId })}</h1>

      {loading || !analysis ? (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Image className="h-5 w-5" />
                  {t('satellite_image_preview')}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <img
                  src={analysis.image_url}
                  alt={`Satellite analysis for task ${analysis.task_id}`}
                  className="w-full h-auto rounded-md object-contain"
                />
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
                <CardHeader>
                  <CardTitle>{t('satellite_analysis_metrics')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">{t('satellite_task_id')}</p>
                      <p>{analysis.task_id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{t('satellite_date_processed')}</p>
                      <p>{new Date(analysis.date_processed).toLocaleDateString()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{t('satellite_area_covered')}</p>
                      <p>{analysis.area_covered_hectares} ha</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{t('satellite_ndvi_mean')}</p>
                      <p>{analysis.ndvi_mean.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{t('satellite_ndvi_std')}</p>
                      <p>{analysis.ndvi_std.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">{t('satellite_anomaly_detected')}</p>
                      <p>{analysis.anomaly_detected ? t('common_yes') : t('common_no')}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {analysis.anomaly_detected && analysis.anomaly_description && (
                <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
                  <CardHeader>
                    <CardTitle className="text-red-500">{t('satellite_anomaly_details')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>{analysis.anomaly_description}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}