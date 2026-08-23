// frontend/app/science/soil/[analysisId]/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, CheckCircle } from 'lucide-react';

interface SoilAnalysisResult {
  id: number;
  sample_id: string;
  date_taken: string;
  ph: number;
  nitrogen: number;
  phosphorus: number;
  potassium: number;
  organic_carbon: number;
  texture: string;
  recommendation: string;
}

export default function SoilAnalysisPage() {
  const params = useParams();
  const { analysisId } = params;
  const { token } = useAuth(); // Assuming API calls need auth token
  const { t } = useI18n();
  const { colors } = useTheme();
  const [analysis, setAnalysis] = useState<SoilAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        // const res = await apiClient.get(`/api/v1/soil/analysis/${analysisId}`);
        // setAnalysis(res.data);
        // Mock data for demonstration
        setAnalysis({
          id: parseInt(analysisId as string),
          sample_id: 'SOIL-2023-1001',
          date_taken: '2023-10-27T10:00:00Z',
          ph: 6.5,
          nitrogen: 120,
          phosphorus: 45,
          potassium: 210,
          organic_carbon: 2.3,
          texture: 'Clay Loam',
          recommendation: 'Add compost to improve nitrogen levels.',
        });
      } catch (err) {
        setError('Failed to load analysis data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (analysisId) {
      fetchAnalysis();
    }
  }, [analysisId, token]);

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
      <h1 className="text-3xl font-bold mb-6">{t('soil_analysis_title', { id: analysisId })}</h1>

      {loading || !analysis ? (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <CardTitle>{t('soil_analysis_details')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_sample_id')}</p>
                  <p>{analysis.sample_id}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_date_taken')}</p>
                  <p>{new Date(analysis.date_taken).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_texture')}</p>
                  <p>{analysis.texture}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_ph')}</p>
                  <p>{analysis.ph.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_nitrogen')}</p>
                  <p>{analysis.nitrogen} ppm</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_phosphorus')}</p>
                  <p>{analysis.phosphorus} ppm</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_potassium')}</p>
                  <p>{analysis.potassium} ppm</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('soil_organic_carbon')}</p>
                  <p>{analysis.organic_carbon}%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                {t('soil_recommendation_title')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p>{analysis.recommendation}</p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}