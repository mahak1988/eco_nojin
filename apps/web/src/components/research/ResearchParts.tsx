import type { ReactNode } from 'react';
import { type DotState, StatusDot } from '@/components/StatusDot';

export interface ResearchFact {
  id: string;
  label: string;
  /** `null` renders the shared unavailable label — never a placeholder value. */
  value: string | null;
}

/** Structured definition list; a missing fact shows the shared unavailable label. */
export function SummaryList({
  items,
  unavailableLabel,
  columns = 2,
}: {
  items: readonly ResearchFact[];
  unavailableLabel: string;
  columns?: 2 | 3 | 4;
}) {
  if (items.length === 0) return null;
  const grid =
    columns === 4
      ? 'sm:grid-cols-2 lg:grid-cols-4'
      : columns === 3
        ? 'sm:grid-cols-2 lg:grid-cols-3'
        : 'sm:grid-cols-2';

  return (
    <dl className={`grid min-w-0 gap-3 ${grid}`}>
      {items.map((fact) => (
        <div key={fact.id} className="min-w-0">
          <dt className="text-xs text-ink-soft">{fact.label}</dt>
          <dd
            className="num mt-1 min-w-0 truncate text-sm text-ink"
            title={fact.value ?? undefined}
          >
            {fact.value ?? unavailableLabel}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export interface ResearchContract {
  id: string;
  label: string;
  /** Registered endpoint, or `null` while the contract is unimplemented. */
  endpoint: string | null;
  state: DotState;
  stateLabel: string;
}

/** Registry contract list: every capability shows its endpoint and its state. */
export function ContractList({
  items,
  endpointLabel,
  unavailableLabel,
}: {
  items: readonly ResearchContract[];
  endpointLabel: string;
  unavailableLabel: string;
}) {
  return (
    <ul className="space-y-2">
      {items.map((contract) => (
        <li
          key={contract.id}
          className="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-m)] border border-[var(--line)] px-4 py-3"
        >
          <span className="min-w-0 text-sm text-ink">{contract.label}</span>
          <span className="flex min-w-0 flex-wrap items-center gap-3">
            <span className="num min-w-0 break-all text-xs text-ink-faint">
              <span className="sr-only">{endpointLabel}: </span>
              {contract.endpoint ?? unavailableLabel}
            </span>
            <StatusDot state={contract.state} label={contract.stateLabel} />
          </span>
        </li>
      ))}
    </ul>
  );
}

export interface ResearchRecord {
  id: string;
  title: ReactNode;
  description?: ReactNode;
  technical?: ReactNode;
  state?: DotState;
  stateLabel?: string;
  facts?: readonly ResearchFact[];
}

/** Live record list; every row may carry its own status and provenance facts. */
export function RecordList({
  label,
  items,
  unavailableLabel,
  emptyLabel,
}: {
  label: string;
  items: readonly ResearchRecord[];
  unavailableLabel: string;
  emptyLabel: string;
}) {
  return (
    <section aria-label={label}>
      <p className="field-label">{label}</p>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-ink-soft">{emptyLabel}</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((record) => (
            <li key={record.id} className="card p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <span className="min-w-0 text-sm text-ink">{record.title}</span>
                {record.state && record.stateLabel ? (
                  <StatusDot state={record.state} label={record.stateLabel} />
                ) : null}
              </div>
              {record.description ? (
                <p className="mt-1 text-xs text-ink-soft">{record.description}</p>
              ) : null}
              {record.technical ? (
                <p className="num mt-1 min-w-0 break-all text-xs text-ink-faint">
                  {record.technical}
                </p>
              ) : null}
              {record.facts && record.facts.length > 0 ? (
                <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                  {record.facts.map((fact) => (
                    <div key={fact.id} className="min-w-0">
                      <dt className="text-xs text-ink-soft">{fact.label}</dt>
                      <dd
                        className="num mt-1 min-w-0 break-all text-xs text-ink"
                        title={fact.value ?? undefined}
                      >
                        {fact.value ?? unavailableLabel}
                      </dd>
                    </div>
                  ))}
                </dl>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Shared honest-state notice; used wherever a registered contract is missing. */
export function UnavailableNotice({
  title,
  detail,
  children,
}: {
  title: string;
  detail: string;
  children?: ReactNode;
}) {
  return (
    <div
      className="card p-4"
      style={{ borderColor: 'color-mix(in oklch, var(--clay) 40%, var(--line))' }}
    >
      <p className="text-sm text-clay">{title}</p>
      <p className="mt-2 text-sm text-ink-soft">{detail}</p>
      {children}
    </div>
  );
}
