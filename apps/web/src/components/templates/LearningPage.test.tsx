import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { LearningPage } from './LearningPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.learning;

describe('T12 Learning', () => {
  it("declares the plan's archetype: step by step, and stamped on its definitions", () => {
    expect(TEMPLATE.plan).toBe('T12');
    expect(TEMPLATE.density).toBe('comfortable');
    expect(TEMPLATE.regions).toContain('navigation');
    // A guide cites its definitions, not an output, so the stamp lands on the
    // detail panel rather than on the data.
    expect(TEMPLATE.provenance.anchor).toBe('detail');
  });

  it('puts the media beside the step, not above it', () => {
    const view = renderTemplate(
      <LearningPage
        {...frameProps()}
        navigation={<ol>STEP 1</ol>}
        media={
          <div role="img" aria-label="DEMO">
            FIGURE
          </div>
        }
        detail={<div>GLOSSARY</div>}
        notes={<div>NEXT STEP</div>}
      />,
    );
    expect(view.region('navigation')?.textContent).toContain('STEP 1');
    expect(view.region('detail')?.textContent).toContain('GLOSSARY');
    expect(view.region('notes')?.textContent).toContain('NEXT STEP');
    // Media is an accessible slot, never an unlabelled decoration.
    expect(view.q('[role="img"]')?.getAttribute('aria-label')).toBe('DEMO');
  });

  it('puts the source stamp on the detail panel', () => {
    const view = renderTemplate(<LearningPage {...frameProps()} detail={<div>GLOSSARY</div>} />);
    expect(view.stampIn('detail')).not.toBeNull();
  });

  it("renders all five of §4.5's states, keeping the steps navigable", () => {
    const views = renderAllStates((state) => (
      <LearningPage {...frameProps({ state })} navigation={<ol>STEP 1</ol>} />
    ));
    expectFiveStates(views);
    for (const view of views) {
      expect(view.region('navigation'), 'a failed guide keeps its steps').not.toBeNull();
    }
  });

  it("uses ResourcePage's render prop for the guide body", () => {
    const view = renderTemplate(
      <LearningPage {...frameProps()} body={({ total }) => <p>{`TOTAL ${total}`}</p>} />,
    );
    expect(view.text()).toContain('TOTAL 3');
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<LearningPage {...frameProps()} />).container);
  });
});
