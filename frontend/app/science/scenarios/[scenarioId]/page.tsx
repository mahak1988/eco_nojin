// frontend/app/science/scenarios/[scenarioId]/page.tsx
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
import { AlertCircle, Play, RotateCcw } from 'lucide-react';

interface ScenarioDetail {
  id: number;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'completed';
  created_at: string;
  updated_at: string;
  parameters: Record<string, any>;
  results?: any; // Could be complex, like simulation outputs
}

export default function ScenarioDetailPage() {
  const params = useParams();
  const { scenarioId } = params;
  const { token } = useAuth();
  const { t } = useI18n();
  const { colors } = useTheme();
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const fetchScenario = async () => {
      try {
        // const res = await apiClient.get(`/api/v1/scenarios/${scenarioId}`);
        // setScenario(res.data);
        // Mock data for demonstration
        setScenario({
          id: parseInt(scenarioId as string),
          name: 'Reforestation Plan A - Updated',
          description: 'Plant native trees in degraded northern area. Optimized for biodiversity.',
          status: 'active',
          created_at: '2023-10-20T10:00:00Z',
          updated_at: '2023-10-30T16:45:00Z',
          parameters: {
            species: 'Oak, Pine',
            area_hectares: 50,
            expected_timeframe_years: 5,
            budget_usd: 10000
          },
          results: {
            estimated_trees_planted: 5000,
            projected_co2_absorbed_tons: 125.5,
            biodiversity_impact_score: 8.7
          }
        });
      } catch (err) {
        setError('Failed to load scenario details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (scenarioId) {
      fetchScenario();
    }
  }, [scenarioId, token]);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    try {
      // const res = await apiClient.post(`/api/v1/scenarios/${scenarioId}/run`);
      // setScenario(prev => ({...prev!, ...res.data}));
      // Mock update on run
      setTimeout(() => {
        setScenario(prev => prev ? {
          ...prev,
          status: 'completed',
          results: {
            estimated_trees_planted: 5000,
            projected_co2_absorbed_tons: 130.2, // Slightly different mock result
            biodiversity_impact_score: 8.9
          }
        } : null);
        setIsRunning(false);
      }, 1500);
    } catch (err) {
      setError('Failed to run simulation.');
      console.error(err);
      setIsRunning(false);
    }
  };

  const handleResetScenario = () => {
    // Logic to reset scenario to draft or initial state
    setScenario(prev => prev ? {...prev, status: 'draft'} : null);
  };

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
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{t('scenario_detail_title', { name: scenario?.name || scenarioId })}</h1>
        <div className="flex space-x-2">
          <Button onClick={handleRunSimulation} disabled={isRunning || scenario?.status === 'completed'}>
            <Play className="mr-2 h-4 w-4" />
            {isRunning ? t('scenario_running') : t('scenario_run_simulation')}
          </Button>
          <Button variant="outline" onClick={handleResetScenario} disabled={scenario?.status !== 'completed'}>
            <RotateCcw className="mr-2 h-4 w-4" />
            {t('scenario_reset')}
          </Button>
        </div>
      </div>

      {loading || !scenario ? (
        <div className="space-y-4">
          <Skeleton className="h-8 w-1/2" />
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <Card style={{ backgroundColor: colors.cardBg, borderColor: colors.border }}>
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold">{t('scenario_parameters')}</h4>
                  <ul className="mt-2 space-y-1">
                    {Object.entries(scenario.parameters).map(([key, value]) => (
                      <li key={key} className="flex justify-between text-sm">
                        <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}:</span>
                        <span>{value}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                {scenario.results && (
                  <div>
                    <h4 className="font-semibold">{t('scenario_results')}</h4>
                    <ul className="mt-2 space-y-1">
                      {Object.entries(scenario.results).map(([key, value]) => (
                        <li key={key} className="flex justify-between text-sm">
                          <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}:</span>
                          <span>{value}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}