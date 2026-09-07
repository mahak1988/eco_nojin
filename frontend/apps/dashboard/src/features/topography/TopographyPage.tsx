import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function TopographyPage() {
  const { t } = useTranslation();
  const [bounds, setBounds] = useState({ south: '35.6', west: '51.3', north: '35.75', east: '51.55' });
  const [resolution, setResolution] = useState('30');
  const [aoiType, setAoiType] = useState<'watershed' | 'farm' | 'plot'>('watershed');

  const run = useRunMotorEndpoint('/api/v1/analyses/topography/');

  function submit() {
    const b = {
      south: Number(bounds.south),
      west: Number(bounds.west),
      north: Number(bounds.north),
      east: Number(bounds.east),
    };
    run.mutate({
      bounds: b,
      resolution_m: Number(resolution),
      aoi_type: aoiType,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.topography.title', '🏔️ Topography')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.topography.subtitle', 'DEM-derived slope / aspect / curvature analysis for watersheds and farms.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.topography.bboxTitle', 'Bounding box (WGS-84)')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-4">
          <Field label={t('dashboard.pages.topography.south', 'South')}>
            <input
              value={bounds.south}
              onChange={(e) => setBounds({ ...bounds, south: (e.target as HTMLInputElement).value })}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.topography.west', 'West')}>
            <input
              value={bounds.west}
              onChange={(e) => setBounds({ ...bounds, west: (e.target as HTMLInputElement).value })}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.topography.north', 'North')}>
            <input
              value={bounds.north}
              onChange={(e) => setBounds({ ...bounds, north: (e.target as HTMLInputElement).value })}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.topography.east', 'East')}>
            <input
              value={bounds.east}
              onChange={(e) => setBounds({ ...bounds, east: (e.target as HTMLInputElement).value })}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.topography.resolution', 'Resolution (m)')}>
            <input
              type="number"
              value={resolution}
              onChange={(e) => setResolution((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.topography.aoiType', 'AOI type')}>
            <select
              value={aoiType}
              onChange={(e) => setAoiType((e.target as HTMLSelectElement).value as typeof aoiType)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="watershed">{t('dashboard.pages.topography.watershed', 'Watershed')}</option>
              <option value="farm">{t('dashboard.pages.topography.farm', 'Farm')}</option>
              <option value="plot">{t('dashboard.pages.topography.plot', 'Plot')}</option>
            </select>
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.topography.runButton', 'Analyze topography')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.topography.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.topography.resultTitle', 'Topography output')}
        subtitle={t('dashboard.pages.topography.resultSubtitle', { aoi: aoiType, resolution, defaultValue: '{{aoi}} • {{resolution}} m' })}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.topography.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}