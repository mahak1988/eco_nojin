// frontend/app/science/watershed/[projectId]/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle, Droplets } from 'lucide-react';

interface WatershedModelResult {
  id: number;
  project_id: string;
  name: string;
  area_sqkm: number;
  rainfall_mm: number;
  runoff_m3: number;
  infiltration_m3: number;
  status: 'active' | 'completed' | 'pending';
  last_updated: string;
}

export default function WatershedProjectPage() {
  const params = useParams();
  const { projectId } = params;
  const { token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [project, setProject] = useState<WatershedModelResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        // const res = await apiClient.get(`/api/v1/watershed/project/${projectId}`);
        // setProject(res.data);
        // Mock data for demonstration
        setProject({
          id: parseInt(projectId as string),
          project_id: 'WAT-PROJ-2023-A01',
          name: 'River Basin Model for Eco Nojin Valley',
          area_sqkm: 45.2,
          rainfall_mm: 120.5,
          runoff_m3: 1250000,
          infiltration_m3: 800000,
          status: 'active',
          last_updated: '2023-10-29T09:15:00Z'
        });
      } catch (err) {
        setError('Failed to load watershed project data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchProject();
    }
  }, [projectId, token]);

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
      <h1 className="text-3xl font-bold mb-6">{t('watershed_project_title', { id: projectId })}</h1>

      {loading || !project ? (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Droplets className="h-5 w-5" />
                {project.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_project_id')}</p>
                  <p>{project.project_id}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_area')}</p>
                  <p>{project.area_sqkm} km²</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_status')}</p>
                  <p>{t(`watershed_status_${project.status}`)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_last_updated')}</p>
                  <p>{new Date(project.last_updated).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_rainfall')}</p>
                  <p>{project.rainfall_mm} mm</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_runoff')}</p>
                  <p>{(project.runoff_m3 / 1000).toFixed(2)} kL</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{t('watershed_infiltration')}</p>
                  <p>{(project.infiltration_m3 / 1000).toFixed(2)} kL</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}