import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function IrrigationDesignPage() {
  const { t } = useTranslation();
  const [crop, setCrop] = useState('wheat');
  const [fieldArea, setFieldArea] = useState('100');
  const [soilType, setSoilType] = useState('loam');
  const [slope, setSlope] = useState('2');
  const [waterSource, setWaterSource] = useState('groundwater');

  const run = useRunMotorEndpoint('/api/v1/analyses/irrigation-design/');

  function submit() {
    run.mutate({
      crop,
      field_area_ha: Number(fieldArea),
      soil_type: soilType,
      slope_pct: Number(slope),
      water_source: waterSource,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.irrigation.title', '💧 Irrigation design')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.irrigation.subtitle', 'Designs drip / sprinkler / surface systems with optimal pipe diameters and pump hours.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.irrigation.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label={t('dashboard.pages.irrigation.crop', 'Crop')}>
            <input
              value={crop}
              onChange={(e) => setCrop((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.irrigation.fieldArea', 'Field area (ha)')}>
            <input
              type="number"
              value={fieldArea}
              onChange={(e) => setFieldArea((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.irrigation.soilType', 'Soil type')}>
            <select
              value={soilType}
              onChange={(e) => setSoilType((e.target as HTMLSelectElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="sand">{t('dashboard.pages.irrigation.soilSand', 'Sand')}</option>
              <option value="loamy_sand">{t('dashboard.pages.irrigation.soilLoamySand', 'Loamy sand')}</option>
              <option value="sandy_loam">{t('dashboard.pages.irrigation.soilSandyLoam', 'Sandy loam')}</option>
              <option value="loam">{t('dashboard.pages.irrigation.soilLoam', 'Loam')}</option>
              <option value="silt_loam">{t('dashboard.pages.irrigation.soilSiltLoam', 'Silt loam')}</option>
              <option value="silt">{t('dashboard.pages.irrigation.soilSilt', 'Silt')}</option>
              <option value="clay_loam">{t('dashboard.pages.irrigation.soilClayLoam', 'Clay loam')}</option>
              <option value="clay">{t('dashboard.pages.irrigation.soilClay', 'Clay')}</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.irrigation.slope', 'Slope (%)')}>
            <input
              type="number"
              value={slope}
              onChange={(e) => setSlope((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.irrigation.waterSource', 'Water source')}>
            <select
              value={waterSource}
              onChange={(e) => setWaterSource((e.target as HTMLSelectElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="groundwater">{t('dashboard.pages.irrigation.waterGroundwater', 'Groundwater')}</option>
              <option value="surface">{t('dashboard.pages.irrigation.waterSurface', 'Surface water')}</option>
              <option value="rainwater">{t('dashboard.pages.irrigation.waterRainwater', 'Rainwater harvesting')}</option>
              <option value="treated_wastewater">{t('dashboard.pages.irrigation.waterTreatedWastewater', 'Treated wastewater')}</option>
            </select>
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.irrigation.submit', 'Design irrigation system')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.irrigation.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.irrigation.resultTitle', 'Irrigation design')}
        subtitle={`${crop} • ${fieldArea} ha • ${soilType}`}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.irrigation.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}