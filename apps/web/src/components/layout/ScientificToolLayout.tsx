'use client';

import { useRouter } from 'next/navigation';
import type { ReactNode } from 'react';
import { StatusDot } from '@/components/StatusDot';
import type { DomainCapabilityState } from '@/lib/domains/registry';

export interface ScientificToolFact {
  id: string;
  label: string;
  /** `null` renders the shared unavailable label — never a placeholder value. */
  value: string | null;
}

export interface ScientificToolLayoutProps {
  /** Technical identifier rendered above the heading. */
  toolId: string;
  title: string;
  lead?: string;
  state: DomainCapabilityState;
  stateLabel: string;
  unavailableLabel: string;
  inputLabel: string;
  outputLabel: string;
  metadataLabel: string;
  replayLabel: string;
  inputPanel: ReactNode;
  outputScene: ReactNode;
  facts: readonly ScientificToolFact[];
  children?: ReactNode;
}

/**
 * T07 — shared shell for every HyDroMa scientific tool.
 *
 * Left: the registered input contract. Right: the output scene. Bottom: the
 * model metadata status bar. Replay re-runs the server render with exactly the
 * same inputs, so a run can be compared without retyping anything.
 *
 * All copy arrives as props: the component never hard-codes visible text, and
 * every fact that has no registered contract renders the shared
 * `statusLine.unavailable` label instead of a number.
 */
export function ScientificToolLayout({
  toolId,
  title,
  lead,
  state,
  stateLabel,
  unavailableLabel,
  inputLabel,
  outputLabel,
  metadataLabel,
  replayLabel,
  inputPanel,
  outputScene,
  facts,
  children,
}: ScientificToolLayoutProps) {
  const router = useRouter();

  return (
    <div className="mx-auto w-full max-w-6xl px-6 pb-16 pt-4">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="num text-xs text-ink-faint">{toolId}</p>
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{title}</h1>
          {lead ? <p className="mt-2 max-w-2xl text-sm text-ink-soft">{lead}</p> : null}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StatusDot state={state === 'available' ? 'ok' : 'down'} label={stateLabel} />
          <button type="button" className="btn btn-ghost" onClick={() => router.refresh()}>
            {replayLabel}
          </button>
        </div>
      </header>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <section className="card p-5" aria-labelledby="scientific-tool-input">
          <h2 id="scientific-tool-input" className="field-label">
            {inputLabel}
          </h2>
          <div className="mt-3">{inputPanel}</div>
        </section>
        <section className="card p-5" aria-labelledby="scientific-tool-output">
          <h2 id="scientific-tool-output" className="field-label">
            {outputLabel}
          </h2>
          <div className="mt-3">{outputScene}</div>
        </section>
      </div>

      <section className="card mt-4 p-5" aria-labelledby="scientific-tool-metadata">
        <h2 id="scientific-tool-metadata" className="field-label">
          {metadataLabel}
        </h2>
        <dl className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {facts.map((fact) => (
            <div key={fact.id} className="min-w-0">
              <dt className="text-xs text-ink-soft">{fact.label}</dt>
              <dd className="num mt-1 truncate text-sm text-ink" title={fact.value ?? undefined}>
                {fact.value ?? unavailableLabel}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      {children}
    </div>
  );
}

export default ScientificToolLayout;
