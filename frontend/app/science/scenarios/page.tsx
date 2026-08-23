// frontend/app/science/scenarios/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useI18n } from '@/lib/i18n-context';
import { useTheme } from '@/lib/theme-context';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { List, Plus, Play, Eye } from 'lucide-react';
import Link from 'next/link';

interface Scenario {
  id: number;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'completed';
  created_at: string;
  updated_at: string;
}

export default function ScenariosPage() {
  const { token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScenarios = async () => {
      try {
        // const res = await apiClient.get('/api/v1/scenarios');
        // setScenarios(res.data);
        // Mock data for demonstration
        setScenarios([
          {
            id: 1,
            name: 'Reforestation Plan A',
            description: 'Plant native trees in degraded northern area.',
            status: 'active',
            created_at: '2023-10-20T10:00:00Z',
            updated_at: '2023-10-25T14:30:00Z',
          },
          {
            id: 2,
            name: 'Water Conservation B',
            description: 'Implement drip irrigation in central plots.',
            status: 'draft',
            created_at: '2023-10-22T11:15:00Z',
            updated_at: '2023-10-22T11:15:00Z',
          },
        ]);
      } catch (err) {
        setError('Failed to load scenarios.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchScenarios();
  }, [token]);

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-6 text-center text-red-700 flex items-center justify-center">
            <List className="h-5 w-5 mr-2" />
            {error}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{t('scenarios_list_title')}</h1>
        <Button asChild>
          <Link href="/science/scenarios/new">
            <Plus className="mr-2 h-4 w-4" /> {t('scenarios_create_new')}
          </Link>
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {scenarios.map((scenario) => (
            <Card key={scenario.id} style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <CardTitle>{scenario.name}</CardTitle>
                  <Badge variant={scenario.status === 'active' ? 'default' : scenario.status === 'draft' ? 'secondary' : 'outline'}>
                    {t(`scenario_status_${scenario.status}`)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">{scenario.description}</p>
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/science/scenarios/${scenario.id}`}>
                      <Eye className="h-4 w-4 mr-2" />
                      {t('common_view')}
                    </Link>
                  </Button>
                  <Button size="sm">
                    <Play className="h-4 w-4 mr-2" />
                    {t('scenarios_run_simulation')}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}