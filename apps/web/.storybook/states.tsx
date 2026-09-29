import type { ReactNode } from 'react';

import { Card, type CardDensity } from '../src/components/ui/Card';
import { type DataState, StateSlot } from '../src/components/ui/StateSlot';
import { partialDetail, STATE_ORDER, stateLabels } from './labels';
/**
 * The five states, rendered the way a page renders them.
 *
 * This is the reason the state requirement is satisfiable at all. The five states
 * are not five props spread across twenty components — they are one vocabulary
 * that `StateSlot` owns, and a component's state is expressed by wrapping it
 * there. So a story that wanted to show "the button while the platform is
 * offline" is not allowed to invent an offline-looking button: it renders the
 * button inside the offline state and lets `StateSlot` say what is true. For most
 * primitives that is the honest answer — in four of the five states the content
 * is genuinely not on the screen, and a story that drew a component in the
 * loading state would be showing something no page can produce.
 */

export interface FiveStatesProps {
  /** What the state is about, in a sentence, for the story reader. */
  title: string;
  /** The component under test, rendered as `children` of the `ready` state. */
  children: ReactNode;
  density?: CardDensity;
  /** Extra line under a state, e.g. why a result is partial. */
  detail?: Partial<Record<DataState, string>>;
  /** Retry affordance on the states that offer one. */
  action?: boolean;
}

export function FiveStates({
  title,
  children,
  density = 'compact',
  detail,
  action,
}: FiveStatesProps) {
  const labels = stateLabels();
  return (
    <section className="eco-frame" aria-label={title}>
      {([...STATE_ORDER, 'ready'] as DataState[]).map((state) => (
        <figure key={state} className="eco-stack" style={{ margin: 0 }}>
          <figcaption className="eco-label">{state}</figcaption>
          <StateSlot
            state={state}
            density={density}
            labels={labels}
            detail={state === 'partial' ? (detail?.partial ?? partialDetail()) : detail?.[state]}
            onRetry={action && (state === 'error' || state === 'offline') ? () => {} : undefined}
          >
            {children}
          </StateSlot>
        </figure>
      ))}
    </section>
  );
}

/** Vertical rhythm for a story body. */
export function Stack({ label, children }: { label?: string; children: ReactNode }) {
  return (
    <div className="eco-frame">
      {label ? <p className="eco-label">{label}</p> : null}
      {children}
    </div>
  );
}

/** A labelled band of related specimens. */
export function Group({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <p className="eco-label">{label}</p>
      {children}
    </div>
  );
}

/** A scrollable box, so a wide table or a long list is photographed as a page. */
export function Scroll({ children }: { children: ReactNode }) {
  return <div className="eco-scroll">{children}</div>;
}

export { Card };
