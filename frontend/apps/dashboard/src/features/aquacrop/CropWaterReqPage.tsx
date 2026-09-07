import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

type CropInput = {
  crop_type: 'wheat' | 'maize' | 'rice' | 'barley' | 'sorghum';
  start: string;
  end: string;
  irrigation: 'full' | 'deficit' | 'rainfed';
  soil_id?: string;
};

export function CropWaterReqPage() {
  const { t } = useTranslation();
  const [cropType, setCropType] = useState<CropInput['crop_type']>('wheat');
  const [start, setStart] = useState('2025-01-01');
  const [end, setEnd] = useState('2025-12-31');
  const [irrigation, setIrrigation] = useState<CropInput['irrigation']>('rainfed');
  const [soilId, setSoilId] = useState('');

  const run = useRunMotorEndpoint('/api/v1/analyses/crop-water-req/');

  function submit() {
    run.mutate({
      crop_type: cropType,
      start,
      end,
      irrigation,
      soil_id: soilId || undefined,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.aquacrop.title', '🌾 AquaCrop — Crop Water Requirement')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.aquacrop.subtitle', 'FAO AquaCrop model. Computes daily biomass + yield under water stress.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.aquacrop.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label={t('dashboard.pages.aquacrop.cropType', 'Crop type')}>
            <select
              value={cropType}
              onChange={(e) => setCropType((e.target as HTMLSelectElement).value as CropInput['crop_type'])}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="wheat">{t('dashboard.pages.aquacrop.cropWheat', 'Wheat')}</option>
              <option value="maize">{t('dashboard.pages.aquacrop.cropMaize', 'Maize')}</option>
              <option value="rice">{t('dashboard.pages.aquacrop.cropRice', 'Rice')}</option>
              <option value="barley">{t('dashboard.pages.aquacrop.cropBarley', 'Barley')}</option>
              <option value="sorghum">{t('dashboard.pages.aquacrop.cropSorghum', 'Sorghum')}</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.aquacrop.start', 'Start')}>
            <input
              type="date"
              value={start}
              onChange={(e) => setStart((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.aquacrop.end', 'End')}>
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.aquacrop.irrigation', 'Irrigation')}>
            <select
              value={irrigation}
              onChange={(e) => setIrrigation((e.target as HTMLSelectElement).value as CropInput['irrigation'])}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="rainfed">{t('dashboard.pages.aquacrop.irrigationRainfed', 'Rainfed')}</option>
              <option value="full">{t('dashboard.pages.aquacrop.irrigationFull', 'Full irrigation')}</option>
              <option value="deficit">{t('dashboard.pages.aquacrop.irrigationDeficit', 'Deficit')}</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.aquacrop.soilProfileId', 'Soil profile ID (optional)')}>
            <input
              value={soilId}
              onChange={(e) => setSoilId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
              placeholder={t('dashboard.pages.aquacrop.soilPlaceholder', 'e.g. SOIL-001')}
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.aquacrop.run', 'Run AquaCrop')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.aquacrop.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.aquacrop.resultTitle', 'Crop water requirement')}
        subtitle={`${cropType} • ${irrigation} • ${start} → ${end}`}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.aquacrop.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}