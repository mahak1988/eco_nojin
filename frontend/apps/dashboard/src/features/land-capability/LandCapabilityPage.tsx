import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function LandCapabilityPage() {
  const { t } = useTranslation();
  const [profileId, setProfileId] = useState('PROFILE-001');

  const run = useRunMotorEndpoint(`/api/v1/land/profiles/${encodeURIComponent(profileId)}/capability-assessment`);

  function submit() {
    run.mutate({});
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.land-capability.title', '🗺️ Land capability')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.land-capability.subtitle', 'USDA 8-class capability classification from soil + terrain attributes.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.land-capability.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="flex items-end gap-3">
          <Field label={t('dashboard.pages.land-capability.profileId', 'Land profile ID')}>
            <input
              value={profileId}
              onChange={(e) => setProfileId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.land-capability.submit', 'Assess capability')}
          </Button>
        </CardBody>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.land-capability.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.land-capability.resultTitle', 'Capability for {{profileId}}', { profileId })}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.land-capability.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}