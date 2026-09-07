import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function LandDrainagePage() {
  const { t } = useTranslation();
  const [profileId, setProfileId] = useState('PROFILE-001');

  const run = useRunMotorEndpoint(`/api/v1/land/profiles/${encodeURIComponent(profileId)}/drainage-analysis`);

  function submit() {
    run.mutate({});
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.land-drainage.title', '🌊 Land drainage')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.land-drainage.subtitle', 'Subsurface drainage design and drainage coefficient estimation.')}
        </p>
      </header>

      <Card>
        <CardBody className="flex items-end gap-3">
          <Field label={t('dashboard.pages.land-drainage.profileId', 'Profile ID')}>
            <input
              value={profileId}
              onChange={(e) => setProfileId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.land-drainage.submit', 'Analyze drainage')}
          </Button>
        </CardBody>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.land-drainage.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.land-drainage.resultTitle', 'Drainage for {{profileId}}', { profileId })}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.land-drainage.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}