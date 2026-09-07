import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function ErosionPage() {
  const { t } = useTranslation();
  const [siteId, setSiteId] = useState('SITE-001');
  const [rainfallErosivity, setR] = useState('2500');
  const [soilErodibility, setK] = useState('0.32');
  const [slopeLength, setL] = useState('100');
  const [slopePct, setS] = useState('5');
  const [coverFactor, setC] = useState('0.4');
  const [practiceFactor, setP] = useState('1');

  const run = useRunMotorEndpoint(`/api/v1/elevation/erosion-effect/${encodeURIComponent(siteId)}`);

  function submit() {
    run.mutate({
      R: Number(rainfallErosivity),
      K: Number(soilErodibility),
      LS: { length_m: Number(slopeLength), slope_pct: Number(slopePct) },
      C: Number(coverFactor),
      P: Number(practiceFactor),
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.erosion.title', '⛰️ RUSLE Erosion')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.erosion.subtitle', 'Revised Universal Soil Loss Equation. A = R × K × LS × C × P (t/ha/yr).')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.erosion.inputs', 'Inputs')}</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label={t('dashboard.pages.erosion.siteId', 'Site ID')}>
            <input
              value={siteId}
              onChange={(e) => setSiteId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.erosion.factorR', 'R — Rainfall erosivity (MJ·mm/ha·h·yr)')}>
            <input
              type="number"
              value={rainfallErosivity}
              onChange={(e) => setR((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.erosion.factorK', 'K — Soil erodibility (t·h/MJ·mm)')}>
            <input
              type="number"
              step="0.01"
              value={soilErodibility}
              onChange={(e) => setK((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.erosion.factorL', 'L — Slope length (m)')}>
            <input
              type="number"
              value={slopeLength}
              onChange={(e) => setL((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.erosion.factorS', 'S — Slope (%)')}>
            <input
              type="number"
              value={slopePct}
              onChange={(e) => setS((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.erosion.factorC', 'C — Cover factor (0–1)')}>
            <input
              type="number"
              step="0.05"
              min={0}
              max={1}
              value={coverFactor}
              onChange={(e) => setC((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label={t('dashboard.pages.erosion.factorP', 'P — Practice factor')}>
            <input
              type="number"
              step="0.05"
              value={practiceFactor}
              onChange={(e) => setP((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            {t('dashboard.pages.erosion.run', 'Run RUSLE')}
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title={t('dashboard.pages.erosion.runFailed', 'Run failed')}>
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={t('dashboard.pages.erosion.resultTitle', 'Erosion estimate')}
        subtitle={`${t('dashboard.pages.erosion.site', 'Site')} ${siteId}`}
        badge={run.isSuccess ? { tone: 'success', label: t('dashboard.pages.erosion.complete', 'Complete') } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}