import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface DetailPageProps extends TemplatePageProps {
  /** The one action for this entity, plus the commit-verb row. */
  actions?: ReactNode;
  /** Standing facts: state, price, counterparty, and the source stamp. */
  summary?: ReactNode;
  /** Documents, history, traceability. */
  detail?: ReactNode;
  /** Caveats the record carries. */
  notes?: ReactNode;
}

/**
 * T04 — the detail page.
 *
 * One entity, a main column for its facts and a sticky rail at the inline end
 * for the things you can do to it. The rail is where the source stamp lives on
 * this archetype, because the numbers a reader is about to act on are the ones
 * in the summary, not the ones in the body.
 *
 * T04 is also the archetype the plan's single-layout defect hurt most: an order
 * record and a soil grid were rendered identically. They are not now.
 */
export function DetailPage({ actions, summary, detail, notes, ...rest }: DetailPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.detail}
      layout="split"
      actions={actions}
      summary={summary}
      detail={detail}
      notes={notes}
    />
  );
}

export default DetailPage;
