import { useEffect, useMemo, useState } from 'react';
import { useModels, useRunModel, type Model } from '@eco/api';
import { loadStaticCatalog, listModels, type ModelMeta } from '@eco/models';
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, Input, Skeleton } from '@eco/ui';

const DOMAINS = [
  { value: 'all', label: 'All' },
  { value: 'soil', label: '🌍 Soil' },
  { value: 'water', label: '💧 Water' },
  { value: 'crop', label: '🌾 Crop' },
  { value: 'carbon', label: '🌱 Carbon' },
  { value: 'climate', label: '🌤️ Climate' },
  { value: 'erosion', label: '⛰️ Erosion' },
  { value: 'optimization', label: '🎯 Optimization' },
  { value: 'hydraulic', label: '🌊 Hydraulic' },
];

export function ModelsPage() {
  useEffect(() => {
    loadStaticCatalog();
  }, []);

  const remote = useModels();
  const run = useRunModel();
  const [domain, setDomain] = useState<string>('all');
  const [search, setSearch] = useState('');

  const staticModels = listModels();
  const staticById = useMemo(
    () => new Map(staticModels.map((m) => [m.id, m])),
    [staticModels],
  );

  const filtered = useMemo(() => {
    const merged: Array<{ id: string; name: string; domain: string; source: string; description?: string; runtime?: number; version?: string }> = [];

    if (remote.data) {
      for (const m of remote.data) {
        const meta = staticById.get(m.id as never);
        merged.push({
          id: m.id,
          name: m.name,
          domain: m.category ?? meta?.domain ?? 'optimization',
          source: meta?.source ?? 'remote',
          description: m.description ?? meta?.description ?? '',
          runtime: meta?.avg_runtime_ms,
          version: meta?.version,
        });
      }
    }

    for (const m of staticModels as ModelMeta[]) {
      if (merged.find((x) => x.id === m.id)) continue;
      merged.push({
        id: m.id,
        name: m.name,
        domain: m.domain,
        source: m.source,
        description: m.description,
        runtime: m.avg_runtime_ms,
        version: m.version,
      });
    }

    return merged
      .filter((m) => domain === 'all' || m.domain === domain)
      .filter((m) =>
        search.trim().length === 0
          ? true
          : `${m.name} ${m.id} ${m.description ?? ''}`.toLowerCase().includes(search.toLowerCase()),
      );
  }, [remote.data, staticModels, staticById, domain, search]);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Scientific models hub</h1>
          <p className="text-sm text-ink-muted">Browse, filter, and run scientific models exposed by the backend.</p>
        </div>
        <Badge tone="brand" variant="soft">{filtered.length} shown</Badge>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Filters</h2>
        </CardHeader>
        <CardBody className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            {DOMAINS.map((d) => (
              <button
                key={d.value}
                type="button"
                onClick={() => setDomain(d.value)}
                className={
                  domain === d.value
                    ? 'rounded-full bg-brand-600 px-3 py-1 text-xs text-white'
                    : 'rounded-full border border-ink/10 px-3 py-1 text-xs text-ink-muted hover:bg-surface-muted'
                }
              >
                {d.label}
              </button>
            ))}
          </div>
          <Input
            placeholder="Search by name or id…"
            value={search}
            onChange={(e) => setSearch((e.target as HTMLInputElement).value)}
          />
        </CardBody>
      </Card>

      {remote.isLoading && filtered.length === 0 && (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      )}

      {filtered.length === 0 && !remote.isLoading && (
        <EmptyState
          title="No models match"
          description="Try clearing filters or check the backend /models/list endpoint."
        />
      )}

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((m) => (
          <Card key={m.id}>
            <CardBody className="flex flex-col gap-2">
              <div className="flex items-start justify-between">
                <h3 className="font-semibold">{m.name}</h3>
                <Badge tone="brand" variant="soft">{m.domain}</Badge>
              </div>
              <p className="text-xs text-ink-muted line-clamp-3">{m.description}</p>
              <div className="flex justify-between text-xs text-ink-subtle">
                <span>v{m.version ?? '—'}</span>
                <span>{m.runtime ? `${m.runtime} ms` : '—'}</span>
                <span>{m.source}</span>
              </div>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => run.mutate({ slug: m.id, inputs: { demo: true } })}
                disabled={run.isPending}
                aria-label={`Run ${m.name}`}
              >
                Run
              </Button>
            </CardBody>
          </Card>
        ))}
      </div>

      {run.data !== undefined && run.data !== null && (
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Last run</h2>
          </CardHeader>
          <CardBody>
            <pre className="overflow-auto text-[11px] text-ink">
              {JSON.stringify(run.data as unknown, null, 2)}
            </pre>
          </CardBody>
        </Card>
      )}

      {run.error && (
        <EmptyState
          title="Run failed"
          description={(run.error as Error).message}
        />
      )}
    </div>
  );
}