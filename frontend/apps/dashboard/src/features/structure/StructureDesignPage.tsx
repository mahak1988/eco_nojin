import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function StructureDesignPage() {
  const { t } = useTranslation();
  const [structureType, setStructureType] = useState<'channel' | 'culvert' | 'drop' | 'weir'>('channel');
  const [discharge, setDischarge] = useState('5');
  const [slope, setSlope] = useState('0.5');
  const [material, setMaterial] = useState('concrete');

  const run = useRunMotorEndpoint('/api/v1/analyses/structure-design/');

  function submit() {
    run.mutate({
      structure_type: structureType,
      discharge_m3s: Number(discharge),
      slope_pct: Number(slope),
      material,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.structure.title', '🛠️ Hydraulic structure design')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.structure.subtitle', 'Designs channels, culverts, drops and weirs to handle a given discharge.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.structure.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label={t('dashboard.pages.structure.structureType', 'Structure type')}>
            <select
              value={structureType}
              onChange={(e) => setStructureType((e.target as HTMLSelectElement).value as typeof structureType)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="channel">{t('dashboard.pages.structure.channel', 'Channel')}</option>
              <option value="culvert">{t('dashboard.pages.structure.culvert', 'Culvert')}</option>
              <option value="drop">{t('dashboard.pages.structure.drop', 'Drop structure')}</option>
              <option value="weir">{t('dashboard.pages.structure.weir', 'Weir')}</option>
            </select>
          </Field>
          <Field label={t('dashboard.pages.structure.discharge', 'Design discharge (m³/s)')}>
            <input
              type="number"
              step="0.1"
              value={discharge}
              onChange={(e) => setDischarge((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.structure.slope', 'Slope (%)')}>
            <input
              type="number"
              step="0.1"
              value={slope}
              onChange={(e) => setSlope((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.structure.material', 'Material')}>
            <select
              value={material}
              onChange={(e) => setMaterial((e.target as HTMLSelectElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="concrete">{t('dashboard.pages.structure.concrete', 'Concrete')}</option>
              <option value="masonry">{t('dashboard.pages.structure.masonry', 'Masonry')}</option>
              <option value="earthen">{t('dashboard.pages.structure.earthen', 'Earthen')}</option>
              <option value="steel">{t('dashboard.pages.structure.steel', 'Steel')}</option>
              <option value="rock">{t('dashboard.pages.structure.rock', 'Rock riprap')}</option>
            </select>
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.structure.runButton', 'Design structure')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.structure.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.structure.resultTitle', { type: structureType.toUpperCase(), defaultValue: '{{type}} design' })}
        subtitle={t('dashboard.pages.structure.resultSubtitle', { discharge, slope, defaultValue: 'Q = {{discharge}} m³/s • slope {{slope}}%' })}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.structure.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}