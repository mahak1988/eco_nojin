import { useState } from 'react';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function StructureDesignPage() {
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
        <h1 className="text-2xl font-semibold">🛠️ Hydraulic structure design</h1>
        <p className="text-sm text-ink-muted">
          Designs channels, culverts, drops and weirs to handle a given discharge.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <Field label="Structure type">
            <select
              value={structureType}
              onChange={(e) => setStructureType((e.target as HTMLSelectElement).value as typeof structureType)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="channel">Channel</option>
              <option value="culvert">Culvert</option>
              <option value="drop">Drop structure</option>
              <option value="weir">Weir</option>
            </select>
          </Field>
          <Field label="Design discharge (m³/s)">
            <input
              type="number"
              step="0.1"
              value={discharge}
              onChange={(e) => setDischarge((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Slope (%)">
            <input
              type="number"
              step="0.1"
              value={slope}
              onChange={(e) => setSlope((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Material">
            <select
              value={material}
              onChange={(e) => setMaterial((e.target as HTMLSelectElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="concrete">Concrete</option>
              <option value="masonry">Masonry</option>
              <option value="earthen">Earthen</option>
              <option value="steel">Steel</option>
              <option value="rock">Rock riprap</option>
            </select>
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            Design structure
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title="Run failed">
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={`${structureType.toUpperCase()} design`}
        subtitle={`Q = ${discharge} m³/s • slope ${slope}%`}
        badge={run.isSuccess ? { tone: 'success', label: 'Complete' } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}