import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface DashboardPageProps extends TemplatePageProps {
  /** The window every figure on the page is computed over. */
  filters?: ReactNode;
  /** Indicators that do not belong in the widget grid. */
  summary?: ReactNode;
  /** The timeline and the drill-down panel. */
  detail?: ReactNode;
  /** What a reader should do with what they just saw. */
  notes?: ReactNode;
}

/**
 * T06 — the dashboard.
 *
 * A window, a grid of panels, and a summary rail. The plan's widget rail lives
 * in `children`, and the reason this archetype exists separately from T08 is
 * that a dashboard is *read* — there is no bulk selection and no row to export,
 * so it must not borrow the management table's dense affordances.
 */
export function DashboardPage({ filters, summary, detail, notes, ...rest }: DashboardPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.dashboard}
      layout="split"
      filters={filters}
      summary={summary}
      detail={detail}
      notes={notes}
    />
  );
}

export default DashboardPage;
