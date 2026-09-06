import { useState } from 'react';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function ErosionPage() {
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
        <h1 className="text-2xl font-semibold">⛰️ RUSLE Erosion</h1>
        <p className="text-sm text-ink-muted">
          Revised Universal Soil Loss Equation. A = R × K × LS × C × P (t/ha/yr).
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label="Site ID">
            <input
              value={siteId}
              onChange={(e) => setSiteId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="R — Rainfall erosivity (MJ·mm/ha·h·yr)">
            <input
              type="number"
              value={rainfallErosivity}
              onChange={(e) => setR((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="K — Soil erodibility (t·h/MJ·mm)">
            <input
              type="number"
              step="0.01"
              value={soilErodibility}
              onChange={(e) => setK((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="L — Slope length (m)">
            <input
              type="number"
              value={slopeLength}
              onChange={(e) => setL((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="S — Slope (%)">
            <input
              type="number"
              value={slopePct}
              onChange={(e) => setS((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="C — Cover factor (0–1)">
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
          <Field label="P — Practice factor">
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
            Run RUSLE
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title="Run failed">
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title="Erosion estimate"
        subtitle={`Site ${siteId}`}
        badge={run.isSuccess ? { tone: 'success', label: 'Complete' } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}