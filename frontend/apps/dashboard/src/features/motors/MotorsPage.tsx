import { useState } from 'react';
import { useRunMotor, useRunMotorChain } from '@eco/api/hooks/use-motors';
import type { MotorKind } from '@eco/api/schema/motors';
import { AQUACROP_META, HECRAS_META, PYWR_META, ROTH_META, RUSLE_META, SWAT_META } from '@eco/models';
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, Spinner } from '@eco/ui';

const ALL_MOTORS: MotorKind[] = ['swat', 'rusle', 'aquacrop', 'rothc', 'pywr', 'hecras', 'optimize'];
const META: Record<MotorKind, { name: string; domain: string }> = {
  swat: { name: SWAT_META.name, domain: SWAT_META.domain },
  rusle: { name: RUSLE_META.name, domain: RUSLE_META.domain },
  aquacrop: { name: AQUACROP_META.name, domain: AQUACROP_META.domain },
  rothc: { name: ROTH_META.name, domain: ROTH_META.domain },
  pywr: { name: PYWR_META.name, domain: PYWR_META.domain },
  hecras: { name: HECRAS_META.name, domain: HECRAS_META.domain },
  optimize: { name: 'NSGA-II Optimizer', domain: 'optimization' },
};

export function MotorsPage() {
  const [motor, setMotor] = useState<MotorKind>('swat');
  const [chain, setChain] = useState<MotorKind[]>(['swat', 'rusle', 'aquacrop', 'rothc']);

  const single = useRunMotor();
  const chained = useRunMotorChain();

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">Scientific motors</h1>
        <p className="text-sm text-ink-muted">
          Single motor or chained pipeline. Backend routes to the C++ core where applicable.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Run a single motor</h2>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2" role="group" aria-label="انتخاب موتور">
              {ALL_MOTORS.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMotor(m)}
                  aria-pressed={motor === m}
                  className={`rounded-md border px-3 py-1.5 text-xs focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:outline-none ${
                    motor === m
                      ? 'border-brand-600 bg-brand-50 text-brand-700'
                      : 'border-ink/10 text-ink-muted hover:bg-surface-muted'
                  }`}
                >
                  {META[m].name}
                </button>
              ))}
            </div>
            <Button
              onClick={() =>
                single.mutate({
                  motor,
                  payload: { demo: true },
                  dry_run: false,
                })
              }
              disabled={single.isPending}
              aria-label={`اجرای ${META[motor].name}`}
            >
              {single.isPending ? <Spinner size="sm" tone="inverse" /> : null}
              Run {META[motor].name}
            </Button>

            {single.data && (
              <div className="rounded-md bg-surface-muted p-3 text-xs">
                <Badge tone="success" variant="soft">
                  {single.data.duration_ms} ms
                </Badge>{' '}
                <span className="ms-2 text-ink-muted">cached={String(single.data.cached)}</span>
                <pre className="mt-2 overflow-auto text-[11px] text-ink">
                  {JSON.stringify(single.data.output, null, 2)}
                </pre>
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold">Run a chain</h2>
          </CardHeader>
          <CardBody className="flex flex-col gap-3">
            <div className="flex flex-wrap gap-2" role="group" aria-label="انتخاب زنجیرهٔ موتورها">
              {ALL_MOTORS.filter((m) => m !== 'optimize').map((m) => {
                const active = chain.includes(m);
                return (
                  <button
                    key={m}
                    type="button"
                    onClick={() =>
                      setChain((c) =>
                        active ? c.filter((x) => x !== m) : [...c, m],
                      )
                    }
                    aria-pressed={active}
                    className={`rounded-md border px-3 py-1.5 text-xs focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:outline-none ${
                      active
                        ? 'border-brand-600 bg-brand-50 text-brand-700'
                        : 'border-ink/10 text-ink-muted hover:bg-surface-muted'
                    }`}
                  >
                    {META[m].name}
                  </button>
                );
              })}
            </div>
            <Button
              variant="secondary"
              onClick={() => chained.mutate({ chain, payload: { demo: true } })}
              disabled={chained.isPending || chain.length === 0}
              aria-label={`اجرای زنجیرهٔ ${chain.length} مرحله‌ای`}
            >
              {chained.isPending ? <Spinner size="sm" /> : null}
              Run {chain.length}-step chain
            </Button>

            {chained.data && (
              <div className="rounded-md bg-surface-muted p-3 text-xs">
                <Badge tone="success" variant="soft">
                  {chained.data.duration_ms} ms total
                </Badge>
                <ol className="mt-2 list-decimal ps-5">
                  {chained.data.steps.map((s) => (
                    <li key={s.motor}>
                      <span className="font-medium">{META[s.motor].name}</span> — {s.duration_ms} ms
                      {s.cached ? ' (cached)' : ''}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {single.error && <EmptyState title="Run failed" description={(single.error as Error).message} />}
    </div>
  );
}