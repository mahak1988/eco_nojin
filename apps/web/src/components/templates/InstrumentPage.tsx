import type { ReactNode } from 'react';

import {
  renderTemplateChildren,
  TEMPLATE_BY_ID,
  type TemplateChildren,
} from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface InstrumentPageProps extends TemplatePageProps {
  /** The registered input contract. Sticks while the output scrolls. */
  input: ReactNode;
  /** The output scene. Defaults to `children`, so `ResourcePage` still works. */
  output?: TemplateChildren;
  /** The window or scenario selector above the input panel. */
  filters?: ReactNode;
  /** Re-run, save this run, share. */
  actions?: ReactNode;
  /** Model version, calibration, confidence interval — and the source stamp. */
  summary?: ReactNode;
  /** The method note: equations, units, known limits. */
  detail?: ReactNode;
  /** The method note rendered under the output scene. */
  notes?: ReactNode;
}

/**
 * T07 — the scientific instrument.
 *
 * The archetype the plan's gap table is about. 110 pages rendered on the same
 * archetype as a bazaar list, and the cure is this: a sticky input contract at
 * the inline start, the output scene beside it, and a metadata bar that always
 * carries model version, calibration and confidence interval whether or not the
 * run produced a number.
 *
 * `children` is the render prop `ResourcePage` already offers, so this template
 * receives the same `{ total, state, path }` the renderer computed and can place
 * the two halves itself. The density is `dense` on purpose: a results table a
 * scientist scans is not a reading page.
 */
export function InstrumentPage({
  input,
  output,
  filters,
  actions,
  summary,
  detail,
  notes,
  ...rest
}: InstrumentPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.instrument}
      layout="wide"
      filters={filters}
      actions={actions}
      summary={summary}
      detail={detail}
      notes={notes}
      preludeLayout="panels"
      prelude={
        <section
          data-region="instrument-input"
          aria-labelledby="region-instrument-input"
          className="min-w-0 lg:sticky lg:top-20 lg:self-start"
        >
          <h2 id="region-instrument-input" className="field-label mb-2">
            {rest.labels.regions.filters}
          </h2>
          {input}
        </section>
      }
    >
      {(context) => (
        <section
          data-region="instrument-output"
          aria-labelledby="region-instrument-output"
          className="min-w-0"
        >
          <h2 id="region-instrument-output" className="field-label mb-2">
            {rest.labels.regions.data}
          </h2>
          {renderTemplateChildren(output ?? rest.children, context)}
        </section>
      )}
    </TemplateFrame>
  );
}

export default InstrumentPage;
