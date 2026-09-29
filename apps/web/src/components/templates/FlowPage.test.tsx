import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { FlowPage } from './FlowPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.flow;

describe('T05 Multi-step flow', () => {
  it("declares the plan's archetype: a stepper, a commit action, a consequence summary", () => {
    expect(TEMPLATE.plan).toBe('T05');
    expect(TEMPLATE.primaryAction?.kind).toBe('submit');
    expect(TEMPLATE.regions).toContain('navigation');
    expect(TEMPLATE.regions).toContain('summary');
    expect(TEMPLATE.provenance.anchor).toBe('summary');
  });

  it('renders the stepper above the form, not buried under it', () => {
    const view = renderTemplate(
      <FlowPage
        {...frameProps()}
        navigation={<ol aria-label="STEPS">STEP1</ol>}
        actions={<div>NEXT</div>}
        summary={<div>COST</div>}
      />,
    );
    const nav = view.region('navigation');
    expect(nav?.textContent).toContain('STEP1');
    expect(nav?.querySelector('ol')?.getAttribute('aria-label')).toBe('STEPS');
    const regions = [...view.container.querySelectorAll('[data-region]')].map((node) =>
      node.getAttribute('data-region'),
    );
    expect(regions.indexOf('navigation')).toBeLessThan(regions.indexOf('data'));
  });

  it('puts the source stamp on the summary of what committing will do', () => {
    const view = renderTemplate(
      <FlowPage {...frameProps()} actions={<div>NEXT</div>} summary={<div>COST</div>} />,
    );
    expect(view.stampIn('summary')).not.toBeNull();
  });

  it("renders all five of §4.5's states without losing the stepper", () => {
    const views = renderAllStates((state) => (
      <FlowPage
        {...frameProps({ state })}
        navigation={<ol>STEP1</ol>}
        actions={<div>NEXT</div>}
        summary={<div>COST</div>}
      />
    ));
    expectFiveStates(views);
    for (const view of views)
      expect(view.region('navigation'), 'a failed step keeps its stepper').not.toBeNull();
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<FlowPage {...frameProps()} />).container);
  });
});
