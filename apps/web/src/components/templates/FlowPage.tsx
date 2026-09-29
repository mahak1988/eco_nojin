import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface FlowPageProps extends TemplatePageProps {
  /** The stepper. `aria-label` and the per-step state come from the caller. */
  navigation?: ReactNode;
  /** Commit and save-for-later. Exactly one primary verb. */
  actions?: ReactNode;
  /** What committing this step will do, and what it will cost. */
  summary?: ReactNode;
  /** Help, terms and the escape hatch out of the flow. */
  detail?: ReactNode;
}

/**
 * T05 — the multi-step flow.
 *
 * A stepper the reader can see the whole of, one form, and a summary of the
 * consequences beside it. This is the archetype the plan wants for checkout, the
 * ten-step bazaar wizard and the account journeys, and the reason those three
 * are not three different implementations of "a form with a next button".
 */
export function FlowPage({ navigation, actions, summary, detail, ...rest }: FlowPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.flow}
      layout="split"
      navigation={navigation}
      actions={actions}
      summary={summary}
      detail={detail}
    />
  );
}

export default FlowPage;
