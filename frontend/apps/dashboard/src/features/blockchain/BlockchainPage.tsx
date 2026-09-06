import { useState } from 'react';
import { apiClient } from '@eco/api/mutator';
import { useMutation } from '@tanstack/react-query';
import { Alert, Badge, Button, Card, CardBody, CardHeader, EmptyState, Field, Skeleton } from '@eco/ui';

type BlockchainCredit = {
  id: string;
  amount_tco2e: number;
  vintage: number;
  standard: string;
  status: string;
};

type BlockchainProject = {
  id: string;
  name: string;
  area_ha: number;
  status: string;
};

export function BlockchainPage() {
  const [projectId, setProjectId] = useState('');

  const credits = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.get<{ items: BlockchainCredit[] }>(
        '/api/v1/blockchain/carbon/credits',
      );
      return data;
    },
  });

  const projects = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.get<{ items: BlockchainProject[] }>(
        '/api/v1/blockchain/carbon/projects',
      );
      return data;
    },
  });

  const verify = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(`/api/v1/blockchain/carbon/projects/${encodeURIComponent(projectId)}/verify`, {});
      return data;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">⛓️ Carbon blockchain ledger</h1>
        <p className="text-sm text-ink-muted">
          On-chain tracking of verified carbon projects and credits (Verra / Gold Standard).
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Projects</h2>
          </CardHeader>
          <CardBody>
            <Button size="sm" onClick={() => projects.mutate()} disabled={projects.isPending}>
              Load projects
            </Button>
            {projects.isPending && <Skeleton className="mt-3 h-20" />}
            {projects.data && (
              <div className="mt-3 space-y-2">
                {projects.data.items.length === 0 ? (
                  <EmptyState title="No projects yet" description="" />
                ) : (
                  projects.data.items.map((p) => (
                    <div key={p.id} className="rounded bg-surface-muted p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{p.name}</span>
                        <Badge tone="info" variant="soft">{p.status}</Badge>
                      </div>
                      <div className="text-xs text-ink-muted">
                        {p.area_ha.toLocaleString()} ha • {p.id}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Credits</h2>
          </CardHeader>
          <CardBody>
            <Button size="sm" onClick={() => credits.mutate()} disabled={credits.isPending}>
              Load credits
            </Button>
            {credits.isPending && <Skeleton className="mt-3 h-20" />}
            {credits.data && (
              <div className="mt-3 space-y-2">
                {credits.data.items.length === 0 ? (
                  <EmptyState title="No credits" description="" />
                ) : (
                  credits.data.items.map((c) => (
                    <div key={c.id} className="rounded bg-surface-muted p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{c.amount_tco2e.toLocaleString()} tCO₂e</span>
                        <Badge tone="success" variant="soft">{c.status}</Badge>
                      </div>
                      <div className="text-xs text-ink-muted">
                        Vintage {c.vintage} • {c.standard}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Verify a project</h2>
        </CardHeader>
        <CardBody className="flex items-end gap-3">
          <Field label="Project ID">
            <input
              value={projectId}
              onChange={(e) => setProjectId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Button
            onClick={() => verify.mutate()}
            disabled={!projectId || verify.isPending}
            size="sm"
          >
            Verify
          </Button>
        </CardBody>
      </Card>

      {verify.error && (
        <Alert tone="danger" title="Verification failed">
          {(verify.error as Error).message}
        </Alert>
      )}
    </div>
  );
}