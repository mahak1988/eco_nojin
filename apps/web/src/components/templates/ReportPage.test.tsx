import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { ReportPage } from './ReportPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.report;

describe('T10 Report / print', () => {
  it("declares the plan's archetype: printed, compact, and anchored on the data", () => {
    expect(TEMPLATE.plan).toBe('T10');
    expect(TEMPLATE.density).toBe('compact');
    expect(TEMPLATE.primaryAction?.kind).toBe('print');
    expect(TEMPLATE.regions).toContain('print');
    expect(TEMPLATE.provenance.anchor).toBe('data');
  });

  it('states the period, the totals and the print masthead', () => {
    const view = renderTemplate(
      <ReportPage
        {...frameProps()}
        filters={<div>Q3 2026</div>}
        summary={<div>TOTAL</div>}
        detail={<div>LINE ITEMS</div>}
        print={<div>PDF</div>}
      />,
    );
    expect(view.region('filters')?.textContent).toContain('Q3 2026');
    expect(view.region('summary')?.textContent).toContain('TOTAL');
    expect(view.region('detail')?.textContent).toContain('LINE ITEMS');
    expect(view.region('print')?.textContent).toContain('PDF');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(
      renderAllStates((state) => <ReportPage {...frameProps({ state })} print={<div>PDF</div>} />),
    );
  });

  it('keeps the period selector on a failure, so the reader can re-run the period', () => {
    const view = renderTemplate(
      <ReportPage {...frameProps({ state: 'error', ok: false })} filters={<div>Q3 2026</div>} />,
    );
    expect(view.region('filters')?.textContent).toContain('Q3 2026');
    expect(view.region('provenance')).not.toBeNull();
  });

  it('puts the stamp on the data region when the figures arrived', () => {
    const view = renderTemplate(<ReportPage {...frameProps({ state: 'ready' })} />);
    expect(view.stampIn('data')).not.toBeNull();
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<ReportPage {...frameProps()} />).container);
  });
});
