import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { DashboardPage } from './DashboardPage';
import {
  ALL_STATES,
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.dashboard;

describe('T06 Dashboard', () => {
  it("declares the plan's archetype: compact, window first, navigated not submitted", () => {
    expect(TEMPLATE.plan).toBe('T06');
    expect(TEMPLATE.density).toBe('compact');
    expect(TEMPLATE.primaryAction?.kind).toBe('navigate');
    expect(TEMPLATE.regions).toContain('filters');
    expect(TEMPLATE.regions).toContain('detail');
  });

  it('has no filter-and-export affordance, which is what separates it from T08', () => {
    const view = renderTemplate(
      <DashboardPage {...frameProps()} filters={<div>WINDOW</div>} summary={<div>KPIS</div>} />,
    );
    expect(view.region('filters')?.textContent).toContain('WINDOW');
    expect(view.region('summary')?.textContent).toContain('KPIS');
    // T06 is read, not managed: it declares no bulk-action region of its own.
    expect(TEMPLATE.regions).not.toContain('actions');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(
      renderAllStates((state) => (
        <DashboardPage {...frameProps({ state })} filters={<div>WINDOW</div>} />
      )),
    );
  });

  it('keeps the indicators on the summary rail on every state', () => {
    for (const state of ALL_STATES) {
      const view = renderTemplate(
        <DashboardPage {...frameProps({ state })} summary={<div>KPIS</div>} />,
      );
      expect(view.stampIn('summary'), `${state} lost the summary stamp`).not.toBeNull();
    }
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<DashboardPage {...frameProps()} />).container);
  });
});
