import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface NarrativePageProps extends TemplatePageProps {
  /** The edge table of contents the plan hangs off the reading column. */
  detail?: ReactNode;
  /** Footnotes, references and the "what this does not claim" block. */
  notes?: ReactNode;
  /** Print-only masthead. Hidden on screen, visible on paper. */
  print?: ReactNode;
}

/**
 * T02 — the narrative page.
 *
 * A single 72ch column inside a wider frame, so the reading measure holds at
 * every viewport. There is no action region on this archetype at all: T02 is
 * the one template in the system with `primaryAction: null`, because a page
 * whose job is to be read must not offer a button that competes with the text.
 */
export function NarrativePage({ detail, notes, print, ...rest }: NarrativePageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.narrative}
      layout="column"
      detail={detail}
      notes={notes}
      print={print}
    />
  );
}

export default NarrativePage;
