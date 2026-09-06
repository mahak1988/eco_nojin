import { useState } from 'react';
import { useRunMotorEndpoint } from '@/hooks/useMotorEndpoint';
import { Alert, Button, Card, CardBody, CardHeader, Field, ResultCard, RunResultView } from '@eco/ui';

export function LandCapabilityPage() {
  const [profileId, setProfileId] = useState('PROFILE-001');

  const run = useRunMotorEndpoint(`/api/v1/land/profiles/${encodeURIComponent(profileId)}/capability-assessment`);

  function submit() {
    run.mutate({});
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">🗺️ Land capability</h1>
        <p className="text-sm text-ink-muted">
          USDA 8-class capability classification from soil + terrain attributes.
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">Inputs</h2>
        </CardHeader>
        <CardBody className="flex items-end gap-3">
          <Field label="Land profile ID">
            <input
              value={profileId}
              onChange={(e) => setProfileId((e.target as HTMLInputElement).value)}
              className="rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm"
            />
          </Field>
          <Button onClick={submit} disabled={run.isPending}>
            {run.isPending && <span className="me-2 h-3 w-3 animate-spin rounded-full border-2 border-white border-r-transparent" />}
            Assess capability
          </Button>
        </CardBody>
      </Card>

      {run.error && (
        <Alert tone="danger" title="Run failed">
          {(run.error as Error).message}
        </Alert>
      )}

      <ResultCard
        title={`Capability for ${profileId}`}
        badge={run.isSuccess ? { tone: 'success', label: 'Complete' } : undefined}
      >
        <RunResultView data={run.data} loading={run.isPending} error={run.error as Error | null} />
      </ResultCard>
    </div>
  );
}