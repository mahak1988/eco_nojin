import { useState } from 'react';
import { useCarbonCalculate, useCarbonProjects, type CarbonProject } from '@eco/api';
import { Alert, Badge, Button, Card, CardBody, CardHeader, EmptyState, Input, Skeleton, Spinner } from '@eco/ui';
import { formatCompact } from '@eco/utils';

export function CarbonPage() {
  const projects = useCarbonProjects();
  const calculate = useCarbonCalculate();

  const [areaHa, setAreaHa] = useState('100');
  const [species, setSpecies] = useState('oak');
  const [years, setYears] = useState('20');
  const [region, setRegion] = useState('');

  function submit() {
    calculate.mutate({
      area_ha: Number(areaHa),
      species,
      years: Number(years),
      region: region || undefined,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">Carbon calculator</h1>
        <p className="text-sm text-ink-muted">CO₂ sequestration and credit estimation via <code className="rounded bg-surface-muted px-1">/carbon/calculate</code>.</p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-4">
          <Field label="Area (ha)">
            <Input
              type="number"
              min={1}
              value={areaHa}
              onChange={(e) => setAreaHa((e.target as HTMLInputElement).value)}
            />
          </Field>
          <Field label="Species">
            <Input
              value={species}
              onChange={(e) => setSpecies((e.target as HTMLInputElement).value)}
              placeholder="oak / pine / mixed"
            />
          </Field>
          <Field label="Years">
            <Input
              type="number"
              min={1}
              max={100}
              value={years}
              onChange={(e) => setYears((e.target as HTMLInputElement).value)}
            />
          </Field>
          <Field label="Region (optional)">
            <Input
              value={region}
              onChange={(e) => setRegion((e.target as HTMLInputElement).value)}
              placeholder="e.g. temperate"
            />
          </Field>
        </CardBody>
        <div className="border-t border-ink/5 p-5">
          <Button onClick={submit} disabled={calculate.isPending}>
            {calculate.isPending && <Spinner size="sm" tone="inverse" />}
            Calculate CO₂ sequestration
          </Button>
        </div>
      </Card>

      {calculate.error && (
        <Alert
          tone="danger"
          variant="soft"
          title="Calculation failed"
        >
          {(calculate.error as Error).message}
        </Alert>
      )}

      {calculate.data && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardBody>
              <div className="text-3xl font-semibold text-brand-700">
                {formatCompact(calculate.data.co2_tons)}
              </div>
              <div className="text-sm text-ink-muted">CO₂ sequestered (t)</div>
              {calculate.data.methodology && (
                <div className="mt-2 text-xs text-ink-subtle">{calculate.data.methodology}</div>
              )}
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <div className="text-3xl font-semibold text-brand-700">
                {formatCompact(calculate.data.credits)}
              </div>
              <div className="text-sm text-ink-muted">Carbon credits</div>
            </CardBody>
          </Card>
          <Card>
            <CardBody>
              <div className="text-3xl font-semibold text-brand-700">
                {calculate.data.revenue_usd != null
                  ? `$${formatCompact(calculate.data.revenue_usd)}`
                  : '—'}
              </div>
              <div className="text-sm text-ink-muted">Estimated revenue (USD)</div>
            </CardBody>
          </Card>
        </div>
      )}

      <section>
        <h2 className="mb-3 text-base font-semibold">Projects</h2>
        {projects.isLoading && (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-28" />
            ))}
          </div>
        )}
        {projects.error && (
          <EmptyState
            title="Could not load projects"
            description={(projects.error as Error).message}
          />
        )}
        {projects.data && projects.data.length > 0 && (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {projects.data.map((p: CarbonProject) => (
              <Card key={p.id}>
                <CardBody className="flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{p.name}</h3>
                    {p.status && (
                      <Badge tone={p.status === 'verified' || p.status === 'issued' ? 'success' : 'neutral'} variant="soft">
                        {p.status}
                      </Badge>
                    )}
                  </div>
                  {p.region && <p className="text-sm text-ink-muted">{p.region}</p>}
                  <div className="flex justify-between text-xs">
                    <span>{p.area_ha?.toLocaleString('fa-IR') ?? '—'} ha</span>
                    <span>{p.co2_tons ?? '—'} tCO₂</span>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-muted">
      {label}
      {children}
    </label>
  );
}