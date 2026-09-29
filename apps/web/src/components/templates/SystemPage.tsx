import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface SystemPageProps extends TemplatePageProps {
  /** The way out: back to a working surface, or a way to continue offline. */
  actions?: ReactNode;
  /** What still works. Deliberately the only thing this archetype lists. */
  notes?: ReactNode;
}

/**
 * T11 — the system page.
 *
 * The calm one. 404, 503, offline, rate limit, client update: a single centred
 * column that says what happened, what still works, and how to get back, and
 * then stops. It has no `filters`, no `summary` and no `detail` region, because
 * a degraded surface is not the place to offer a reader more to explore.
 */
export function SystemPage({ actions, notes, ...rest }: SystemPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.system}
      layout="column"
      actions={actions}
      notes={notes}
    />
  );
}

export default SystemPage;
