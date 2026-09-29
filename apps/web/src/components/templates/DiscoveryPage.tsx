import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface DiscoveryPageProps extends TemplatePageProps {
  /** Search, facets and sort. Sticks to the top of the scroll container. */
  filters?: ReactNode;
  /** The action rail above the grid: compare, save, clear. */
  actions?: ReactNode;
  /** What the result count means, and what is excluded from it. */
  notes?: ReactNode;
}

/**
 * T03 — the discovery page.
 *
 * A wide frame with a filter bar that stays put and a grid underneath. The
 * difference from T04 is not the columns, it is the intent: nothing here is a
 * record, so there is no summary rail and no per-item document tab. The filter
 * region is the only sticky thing on the page, which is what makes a long list
 * of mixed results still navigable.
 */
export function DiscoveryPage({ filters, actions, notes, ...rest }: DiscoveryPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.discovery}
      layout="wide"
      filters={filters}
      actions={actions}
      notes={notes}
    />
  );
}

export default DiscoveryPage;
