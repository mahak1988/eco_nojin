import type { ReactNode } from 'react';

export type DotState = 'ok' | 'warn' | 'down';

/**
 * StatusDot — live service state indicator (pure CSS, respects
 * prefers-reduced-motion via the global motion budget).
 * i18n of the label is handled by the caller.
 */
export function StatusDot({ state, label }: { state: DotState; label: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs" role="status">
      <span className="status-dot" data-state={state} aria-hidden="true" />
      <span
        className={state === 'ok' ? 'text-moss' : state === 'warn' ? 'text-copper' : 'text-clay'}
      >
        {label}
      </span>
    </span>
  );
}
