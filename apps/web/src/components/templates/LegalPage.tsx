import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface LegalPageProps extends TemplatePageProps {
  /** The diff against the previous version, and the acceptance record. */
  detail?: ReactNode;
  /** Print-only masthead with the version and the effective date. */
  print?: ReactNode;
  /** Notes on jurisdiction and on what the text does not cover. */
  notes?: ReactNode;
}

/**
 * T09 — the legal document.
 *
 * Numbered clauses, a visible version, and a print stylesheet. Like T02 this
 * archetype has no action region and no primary action: a legal text offers
 * nothing to click except itself. The difference from T02 is the clause
 * numbering and the version history, which is why the two are separate
 * archetypes and not one "document" template with a flag.
 */
export function LegalPage({ detail, print, notes, ...rest }: LegalPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.legal}
      layout="column"
      detail={detail}
      print={print}
      notes={notes}
    />
  );
}

export default LegalPage;
