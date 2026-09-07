import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function RunoffPage() {
  const { t } = useTranslation();
  const [watershedId, setWatershedId] = useState('WS-001');
  const [rainfallScenario, setRainfallScenario] = useState('10yr');
  const [start, setStart] = useState('2025-01-01');
  const [end, setEnd] = useState('2025-12-31');

  const run = useRunMotorEndpoint('/api/v1/analyses/runoff/');

  function submit() {
    run.mutate({
      watershed_id: watershedId,
      rainfall_scenario: rainfallScenario,
      start,
      end,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.runoff.title', '💧 SWAT+ Runoff')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.runoff.subtitle', 'Soil & Water Assessment Tool — daily runoff / sediment / nutrient cycles per sub-basin.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.runoff.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label={t('dashboard.pages.runoff.watershedId', 'Watershed ID')}>
            <input
              value={watershedId}
              onChange={(e) => setWatershedId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.runoff.rainfallScenario', 'Rainfall scenario')}>
            <select
              value={rainfallScenario}
              onChange={(e) => setRainfallScenario((e.target as HTMLSelectElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="2yr">{t('dashboard.pages.runoff.scenario2yr', '2-yr')}</option>
              <option value="5yr">{t('dashboard.pages.runoff.scenario5yr', '5-yr')}</option>
              <option value="10yr">{t('dashboard.pages.runoff.scenario10yr', '10-yr')}</option>
              <option value="25yr">{t('dashboard.pages.runoff.scenario25yr', '25-yr')}</option>
              <option value="50yr">{t('dashboard.pages.runoff.scenario50yr', '50-yr')}</option>
              <option value="100yr">{t('dashboard.pages.runoff.scenario100yr', '100-yr')}</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.runoff.start', 'Start')}>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.runoff.end', 'End')}>
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.runoff.submit', 'Run SWAT+')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.runoff.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.runoff.resultTitle', 'Runoff output')}
        subtitle={`${watershedId} • ${rainfallScenario} • ${start} → ${end}`}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.runoff.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}