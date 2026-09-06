import { useState } from 'react';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function SoilCarbonPage() {
  const [clayPct, setClayPct] = useState('25');
  const [socInitial, setSocInitial] = useState('50');
  const [temperature, setTemperature] = useState('15');
  const [rainfall, setRainfall] = useState('400');
  const [years, setYears] = useState('20');
  const [landUse, setLandUse] = useState('cropland');

  const run = useRunMotorEndpoint('/api/v1/carbon/soil-carbon');

  function submit() {
    run.mutate({
      clay_pct: Number(clayPct),
      soc_initial: Number(socInitial),
      temperature: Number(temperature),
      rainfall: Number(rainfall),
      years: Number(years),
      land_use: landUse,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">🌍 RothC Soil Carbon</h1>
        <p className="text-sm text-ink-muted">
          26.4-year Rothamsted carbon turnover model. Outputs final SOC + CO₂ flux.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label="Clay (%)">
            <input
              type="number"
              min={0}
              max={100}
              value={clayPct}
              onChange={(e) => setClayPct((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Initial SOC (tC/ha)">
            <input
              type="number"
              min={0}
              value={socInitial}
              onChange={(e) => setSocInitial((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Mean annual T (°C)">
            <input
              type="number"
              value={temperature}
              onChange={(e) => setTemperature((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Mean annual rainfall (mm)">
            <input
              type="number"
              value={rainfall}
              onChange={(e) => setRainfall((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Years">
            <input
              type="number"
              min={1}
              max={100}
              value={years}
              onChange={(e) => setYears((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Land use">
            <select
              value={landUse}
              onChange={(e) => setLandUse((e.target as HTMLSelectElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="cropland">Cropland</option>
              <option value="grassland">Grassland</option>
              <option value="forest">Forest</option>
              <option value="shrubland">Shrubland</option>
              <option value="bare">Bare</option>
            </select>
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            Run RothC
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title="Run failed">
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title="Soil carbon trajectory"
        subtitle={`${landUse} • ${years} years • ${temperature}°C`}
        badge={run.isSuccess ? { tone: 'success', label: 'Complete' } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}