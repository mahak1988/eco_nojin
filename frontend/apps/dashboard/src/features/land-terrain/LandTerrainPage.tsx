import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function LandTerrainPage() {
  const { t } = useTranslation();
  const [profileId, setProfileId] = useState('PROFILE-001');

  const run = useRunMotorEndpoint(`/api/v1/land/profiles/${encodeURIComponent(profileId)}/terrain-analysis`);

  function submit() {
    run.mutate({});
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.land-terrain.title', '⛰️ Land terrain analysis')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.land-terrain.subtitle', 'DEM-based terrain attributes (slope, aspect, TWI, hillshade).')}
        </p>
      </header>

      <Card>
        <CardBody className="flex items-end gap-3">
          <Field label={t('dashboard.pages.land-terrain.profileId', 'Profile ID')}>
            <input
              value={profileId}
              onChange={(e) => setProfileId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.land-terrain.submit', 'Analyze terrain')}
          </Button>
        </CardBody>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.land-terrain.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.land-terrain.resultTitle', 'Terrain for {{profileId}}', { profileId })}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.land-terrain.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}