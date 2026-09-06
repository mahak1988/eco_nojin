import { useState } from 'react';
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
        <h1 className="text-2xl font-semibold">🌾 AquaCrop — Crop Water Requirement</h1>
        <p className="text-sm text-ink-muted">
          FAO AquaCrop model. Computes daily biomass + yield under water stress.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label="Crop type">
            <select
              value={cropType}
              onChange={(e) => setCropType((e.target as HTMLSelectElement).value as CropInput['crop_type'])}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="wheat">Wheat</option>
              <option value="maize">Maize</option>
              <option value="rice">Rice</option>
              <option value="barley">Barley</option>
              <option value="sorghum">Sorghum</option>
            </select>
          </Field>
          <Field label="Start">
            <input
              type="date"
              value={start}
              onChange={(e) => setStart((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="End">
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Irrigation">
            <select
              value={irrigation}
              onChange={(e) => setIrrigation((e.target as HTMLSelectElement).value as CropInput['irrigation'])}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="rainfed">Rainfed</option>
              <option value="full">Full irrigation</option>
              <option value="deficit">Deficit</option>
            </select>
          </Field>
          <Field label="Soil profile ID (optional)">
            <input
              value={soilId}
              onChange={(e) => setSoilId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
              placeholder="e.g. SOIL-001"
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            Run AquaCrop
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title="Run failed">
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title="Crop water requirement"
        subtitle={`${cropType} • ${irrigation} • ${start} → ${end}`}
        badge={run.isSuccess ? { tone: 'success', label: 'Complete' } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}