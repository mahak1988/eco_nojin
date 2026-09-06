import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@eco/api/mutator';
import { Alert, Badge, Button, Card, CardBody, CardHeader, EmptyState, Skeleton, Spinner } from '@eco/ui';

type CarbonBudgetResult = {
  report_id?: string;
  total_co2e?: number;
  breakdown?: Record<string, number>;
  generated_at?: string;
  [key: string]: unknown;
};

export function MrvPage() {
  const budget = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<CarbonBudgetResult>('/mrv/carbon-budget', {});
      return data;
    },
  });

  const verify = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<{ verified?: number; total?: number }>(
        '/mrv/verify',
        {},
      );
      return data;
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">✅ Monitoring, Reporting &amp; Verification</h1>
        <p className="text-sm text-ink-muted">
          Field-truthed verification for Verra/Gold-Standard carbon claims via <code className="rounded bg-surface-muted px-1">/mrv/*</code>.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Carbon budget report</h2>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <p className="text-sm text-ink-muted">
              Aggregate ground observations into a defensible budget per Verra VM0007.
            </p>
            <Button onClick={() => budget.mutate()} disabled={budget.isPending}>
              {budget.isPending && <Spinner size="sm" tone="inverse" />}
              Generate carbon budget
            </Button>
            {budget.error && (
              <Alert tone="danger" title="Budget generation failed">
                {(budget.error as Error).message}
              </Alert>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Batch verification</h2>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <p className="text-sm text-ink-muted">
              Verify the latest observation queue and return the breakdown.
            </p>
            <Button variant="secondary" onClick={() => verify.mutate()} disabled={verify.isPending}>
              {verify.isPending && <Spinner size="sm" />}
              Verify queue
            </Button>
            {verify.error && (
              <Alert tone="danger" title="Verification failed">
                {(verify.error as Error).message}
              </Alert>
            )}
          </CardBody>
        </Card>
      </div>

      <section>
        <h2 className="mb-3 text-base font-semibold">Last budget</h2>
        {budget.isPending ? (
          <Skeleton className="h-40" />
        ) : !budget.data ? (
          <EmptyState
            title="No budget generated yet"
            description="Click 'Generate carbon budget' to create one."
          />
        ) : (
          <Card>
            <CardBody>
              <div className="mb-3 flex items-center gap-3 text-sm">
                <Badge tone="brand" variant="soft">
                  ID: {budget.data.report_id ?? '—'}
                </Badge>
                {budget.data.generated_at && (
                  <span className="text-ink-muted">
                    Generated {new Date(budget.data.generated_at).toLocaleString()}
                  </span>
                )}
                {typeof budget.data.total_co2e === 'number' && (
                  <span className="ms-auto text-lg font-semibold text-brand-700">
                    {budget.data.total_co2e.toLocaleString()} tCO₂e
                  </span>
                )}
              </div>
              {budget.data.breakdown && Object.keys(budget.data.breakdown).length > 0 ? (
                <div className="grid gap-2 md:grid-cols-3">
                  {Object.entries(budget.data.breakdown).map(([k, v]) => (
                    <div key={k} className="rounded bg-surface-muted p-3 text-sm">
                      <div className="text-ink-muted">{k}</div>
                      <div className="font-semibold text-brand-700">
                        {typeof v === 'number' ? v.toLocaleString() : String(v)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <pre className="overflow-auto text-[11px] text-ink">
                  {JSON.stringify(budget.data, null, 2)}
                </pre>
              )}
            </CardBody>
          </Card>
        )}
      </section>
    </div>
  );
}