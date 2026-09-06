import { useState } from 'react';
import { apiClient } from '@eco/api/mutator';
import { useMutation } from '@tanstack/react-query';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function CarbonOraclePage() {
  const [projectId, setProjectId] = useState('demo-project');

  const issue = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(
        `/api/v1/carbon/projects/${encodeURIComponent(projectId)}/issue`,
        {},
      );
      return data;
    },
  });

  const oracle = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.get(
        `/api/v1/carbon/projects/${encodeURIComponent(projectId)}/oracle-report`,
      );
      return data;
    },
  });

  const verify = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post(
        `/api/v1/carbon/projects/${encodeURIComponent(projectId)}/verify`,
        {},
      );
      return data;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">🌱 Carbon project actions</h1>
        <p className="text-sm text-ink-muted">
          Issue, verify and inspect oracle reports for a carbon project.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Target project</h2>
        </CardHeader>
        <CardBody className="flex items-end gap-3">
          <Field label="Project ID">
            <input
              value={projectId}
              onChange={(e) => setProjectId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => verify.mutate()} disabled={!projectId || verify.isPending}>
              Verify
            </Button>
            <Button size="sm" variant="secondary" onClick={() => issue.mutate()} disabled={!projectId || issue.isPending}>
              Issue credits
            </Button>
            <Button size="sm" onClick={() => oracle.mutate()} disabled={!projectId || oracle.isPending}>
              Oracle report
            </Button>
          </div>
        </CardBody>
      </Card>

      {(verify.error ?? issue.error ?? oracle.error) && (
        <Alert tone="danger" title="Action failed">
          {(verify.error ?? issue.error ?? oracle.error) instanceof Error
            ? (verify.error ?? issue.error ?? oracle.error)?.message
            : 'Unknown error'}
        </Alert>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <ResultCard title="Verification" badge={verify.isSuccess ? { tone: 'success', label: 'OK' } : undefined}>
          <RunResultView data={verify.data} loading={verify.isPending} />
        </ResultCard>
        <ResultCard title="Issuance" badge={issue.isSuccess ? { tone: 'success', label: 'OK' } : undefined}>
          <RunResultView data={issue.data} loading={issue.isPending} />
        </ResultCard>
        <ResultCard title="Oracle report" badge={oracle.isSuccess ? { tone: 'success', label: 'OK' } : undefined}>
          <RunResultView data={oracle.data} loading={oracle.isPending} />
        </ResultCard>
      </div>
    </div>
  );
}