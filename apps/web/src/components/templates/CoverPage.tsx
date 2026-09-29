import type { ReactNode } from 'react';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface CoverPageProps extends TemplatePageProps {
  /**
   * The cover's two ways in. The plan allows exactly two on T01, and this
   * template renders one column of them rather than a page of links.
   */
  actions?: ReactNode;
}

/**
 * T01 — the cover.
 *
 * The only uncapped, full-bleed surface in the system. No side rail, no table,
 * no secondary navigation: the reader is deciding where to go, so the only
 * things on the page are the two ways in and what is actually live.
 */
export function CoverPage({ actions, ...rest }: CoverPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.cover}
      layout="hero"
      actions={actions}
      titleClassName="display max-w-3xl text-4xl font-bold text-balance text-ink sm:text-6xl"
    />
  );
}

export default CoverPage;
