import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface LedgerPageProps extends TemplatePageProps {
  /** Saved views, column picker, the bulk-selection toolbar. */
  filters?: ReactNode;
  /** Bulk verbs: export, assign, approve, archive. */
  actions?: ReactNode;
  /** The row detail drawer. */
  detail?: ReactNode;
}

/**
 * T08 — the management table.
 *
 * Filters above a dense grid, one row per thing, a drawer for the selected row.
 * The whole archetype is built to be scanned rather than read, so its density is
 * `dense` and its regions exclude `summary` and `notes`: a table has no prose
 * and no standing summary, and giving it one is how an admin page ends up
 * looking like a document.
 *
 * §6.4 of the plan is explicit that the entire admin context is this archetype,
 * with a command rail and a hedger. The partition test is what stops "all
 * admin is T08" from quietly becoming "all admin is whatever T08 was".
 */
export function LedgerPage({ filters, actions, detail, ...rest }: LedgerPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.ledger}
      layout="wide"
      filters={filters}
      actions={actions}
      detail={detail}
    />
  );
}

export default LedgerPage;
