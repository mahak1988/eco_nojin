import { useState } from 'react';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function GroundwaterPage() {
  const [aquiferType, setAquiferType] = useState<'confined' | 'unconfined'>('unconfined');
  const [recharge, setRecharge] = useState('50');
  const [abstraction, setAbstraction] = useState('30');
  const [porosity, setPorosity] = useState('0.25');
  const [specificYield, setSy] = useState('0.15');

  const run = useRunMotorEndpoint('/api/v1/analyses/groundwater/');

  function submit() {
    run.mutate({
      aquifer_type: aquiferType,
      recharge_mm_yr: Number(recharge),
      abstraction_mm_yr: Number(abstraction),
      porosity: Number(porosity),
      specific_yield: Number(specificYield),
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">💧 Groundwater balance</h1>
        <p className="text-sm text-ink-muted">
          Computes net recharge and water table change for confined/unconfined aquifers.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-3">
          <Field label="Aquifer type">
            <select
              value={aquiferType}
              onChange={(e) => setAquiferType((e.target as HTMLSelectElement).value as 'confined' | 'unconfined')}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            >
              <option value="unconfined">Unconfined</option>
              <option value="confined">Confined</option>
            </select>
          </Field>
          <Field label="Recharge (mm/yr)">
            <input
              type="number"
              value={recharge}
              onChange={(e) => setRecharge((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Abstraction (mm/yr)">
            <input
              type="number"
              value={abstraction}
              onChange={(e) => setAbstraction((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Porosity (0–1)">
            <input
              type="number"
              step="0.01"
              min={0}
              max={1}
              value={porosity}
              onChange={(e) => setPorosity((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Field label="Specific yield (0–1)">
            <input
              type="number"
              step="0.01"
              min={0}
              max={1}
              value={specificYield}
              onChange={(e) => setSy((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            Run groundwater model
          </Button>
        </div>
      </Card>

      {run.error && (
        <Alert tone="danger" title="Run failed">
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title="Groundwater balance"
        subtitle={`${aquiferType} aquifer`}
        badge={run.isSuccess ? { tone: 'success', label: 'Complete' } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}