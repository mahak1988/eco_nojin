import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

type SatInput = {
  farm_id: string;
  source: 'sentinel2' | 'sentinel1' | 'landsat8' | 'modis';
  index: 'NDVI' | 'NDWI' | 'EVI' | 'LAI' | 'SAVI';
  start: string;
  end: string;
};

export function SatelliteAnalyzePage() {
  const { t } = useTranslation();
  const [farmId, setFarmId] = useState('FARM-001');
  const [source, setSource] = useState<SatInput['source']>('sentinel2');
  const [index, setIndex] = useState<SatInput['index']>('NDVI');
  const [start, setStart] = useState('2025-01-01');
  const [end, setEnd] = useState('2025-12-31');

  const run = useRunMotorEndpoint('/api/v1/satellite/analyze');

  function submit() {
    run.mutate({ farm_id: farmId, source, index, start, end });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.satellite-analyze.title', '🛰️ Satellite index analysis')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.satellite-analyze.subtitle', 'Cloud-masked composites + per-pixel NDVI/NDWI/EVI/LAI/SAVI summaries.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.satellite-analyze.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label={t('dashboard.pages.satellite-analyze.farmId', 'Farm ID')}>
            <input
              value={farmId}
              onChange={(e) => setFarmId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.satellite-analyze.source', 'Source')}>
            <select
              value={source}
              onChange={(e) => setSource((e.target as HTMLSelectElement).value as SatInput['source'])}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="sentinel2">Sentinel-2</option>
              <option value="sentinel1">Sentinel-1 (SAR)</option>
              <option value="landsat8">Landsat 8</option>
              <option value="modis">MODIS</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.satellite-analyze.index', 'Index')}>
            <select
              value={index}
              onChange={(e) => setIndex((e.target as HTMLSelectElement).value as SatInput['index'])}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="NDVI">NDVI</option>
              <option value="NDWI">NDWI</option>
              <option value="EVI">EVI</option>
              <option value="LAI">LAI</option>
              <option value="SAVI">SAVI</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.satellite-analyze.start', 'Start')}>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.satellite-analyze.end', 'End')}>
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
            {t('dashboard.pages.satellite-analyze.analyze', 'Analyze')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.satellite-analyze.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.satellite-analyze.resultTitle', { index, defaultValue: '{{index}} analysis' })}
        subtitle={t('dashboard.pages.satellite-analyze.resultSubtitle', { source, farmId, defaultValue: '{{source}} • farm {{farmId}}' })}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.satellite-analyze.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}