import type { ReactNode } from 'react';

import {
  renderTemplateChildren,
  TEMPLATE_BY_ID,
  type TemplateChildren,
} from '@/lib/design/page-templates';

import { TemplateFrame, type TemplatePageProps } from './TemplateFrame';

export interface LearningPageProps extends TemplatePageProps {
  /** The step list, the section tree, or the chapter index. */
  navigation?: ReactNode;
  /** The media: a video, a diagram, a worked example. */
  media?: ReactNode;
  /** The vocabulary panel, and the stamp that goes with it. */
  detail?: ReactNode;
  /** "What you should be able to do next", and where to go. */
  notes?: ReactNode;
  /** The guide body. Defaults to `children`. */
  body?: TemplateChildren;
}

/**
 * T12 — the learning page.
 *
 * The plan's guidance archetype: step by step, media beside the step, vocabulary
 * underneath, and a next step at the end. It is also the archetype the plan
 * assigns to USSD, SMS and voice, which is the whole point of the §5.3
 * inclusive-access rule — a farmer on a feature phone gets the same designed
 * guidance as somebody on a laptop, not a stripped-down desktop page.
 *
 * The source stamp anchors to `detail` here rather than to the data, because
 * what a guide cites is its definition and its source, not its output.
 */
export function LearningPage({
  media,
  body,
  navigation,
  detail,
  notes,
  ...rest
}: LearningPageProps) {
  return (
    <TemplateFrame
      {...rest}
      template={TEMPLATE_BY_ID.learning}
      layout="wide"
      navigation={navigation}
      detail={detail}
      notes={notes}
    >
      {(context) => (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="min-w-0">{renderTemplateChildren(body ?? rest.children, context)}</div>
          <div className="min-w-0">{media}</div>
        </div>
      )}
    </TemplateFrame>
  );
}

export default LearningPage;
