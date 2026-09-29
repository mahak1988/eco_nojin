import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface ReportPageProps extends TemplatePageProps {
  /** The period selector. A report without a stated period is a lie. */
  filters?: ReactNode;
  /** Totals and the running reconciliation. */
  summary?: ReactNode;
  /** The line-item breakdown. */
  detail?: ReactNode;
  /** Print-only masthead and the download control. */
  print?: ReactNode;
}

/**
 * T10 — the report.
 *
 * A wide frame, because a table of line items does not belong in a reading
 * column, plus a print region that carries the period, the version and the
 * source stamp. The plan insists the period appears on the page itself rather
 * than in a filename, so `filters` is not optional on a report even when there
 * is only one period available.
 */
export function ReportPage({ filters, summary, detail, print, ...rest }: ReportPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.report}
      layout="wide"
      filters={filters}
      summary={summary}
      detail={detail}
      print={print}
    />
  );
}

export default ReportPage;
