import type { ReactNode } from 'react';

import { Card, type CardDensity } from './Card';

/**
 * The five states the master plan requires every data-bearing component to
 * render: loading, empty, error, partial and offline.
 *
 * Implementing them once here is what makes that rule enforceable. Previously
 * each page improvised its own missing-data copy, which is why the same route
 * could say "no data" on one state and "unavailable" on another, and why a
 * genuinely offline reader was shown an error that implied the server was at
 * fault.
 *
 * Every label is a required prop. This component never invents copy: a component
 * library that carries its own English strings cannot be translated, which is
 * the defect the 53 public pages had.
 */

export type DataState = 'ready' | 'loading' | 'empty' | 'error' | 'partial' | 'offline';

export interface StateLabels {
  loading: string;
  empty: string;
  error: string;
  offline: string;
  partial: string;
  /** Announced after the primary state message, e.g. a retry affordance. */
  action?: string;
}

export interface StateSlotProps {
  state: DataState;
  labels: StateLabels;
  /** Rendered only when `state` is `ready` or `partial`. */
  children: ReactNode;
  density?: CardDensity;
  /** Explains a `partial` result, e.g. "showing 3 of 51". */
  detail?: string;
  className?: string;
  onRetry?: () => void;
}

const TONE: Record<Exclude<DataState, 'ready'>, 'neutral' | 'warn' | 'bad'> = {
  loading: 'neutral',
  empty: 'neutral',
  error: 'bad',
  partial: 'warn',
  offline: 'warn',
};

const MARK: Record<Exclude<DataState, 'ready'>, string> = {
  loading: '…',
  empty: '○',
  error: '✕',
  partial: '◐',
  offline: '⌁',
};

const container: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 'var(--space-3)',
  textAlign: 'center',
  minHeight: '8rem',
  padding: 'var(--space-6)',
  color: 'var(--color-ink-soft)',
};

const markStyle = (tone: 'neutral' | 'warn' | 'bad'): React.CSSProperties => ({
  fontSize: '1.5rem',
  lineHeight: 1,
  color:
    tone === 'bad'
      ? 'var(--color-clay)'
      : tone === 'warn'
        ? 'var(--color-copper)'
        : 'var(--color-ink-faint)',
});

/**
 * Renders its children when there is data, and an explicit, labelled
 * explanation when there is not.
 *
 * `partial` is deliberately distinct from `ready`: a page that loaded three of
 * fifty-one rows must say so rather than presenting itself as complete, which is
 * the difference between a declared limit and a silent omission.
 */
export function StateSlot({
  state,
  labels,
  children,
  density = 'cozy',
  detail,
  className = '',
  onRetry,
}: StateSlotProps) {
  if (state === 'ready') {
    return <>{children}</>;
  }

  const tone = TONE[state];
  const message = state === 'partial' ? labels.partial : labels[state];

  return (
    <Card density={density} className={className}>
      <div style={container} role={state === 'error' ? 'alert' : 'status'} aria-live="polite">
        <span style={markStyle(tone)} aria-hidden="true">
          {MARK[state]}
        </span>
        <p style={{ margin: 0, color: 'var(--color-ink)' }}>{message}</p>
        {detail ? <p style={{ margin: 0, fontSize: '0.875rem' }}>{detail}</p> : null}
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            style={{
              background: 'var(--color-forest)',
              color: 'var(--color-on-action)',
              border: 0,
              borderRadius: 'var(--radius-s)',
              padding: 'var(--space-2) var(--space-4)',
              cursor: 'pointer',
            }}
          >
            {labels.action}
          </button>
        ) : null}
      </div>
    </Card>
  );
}

export default StateSlot;
