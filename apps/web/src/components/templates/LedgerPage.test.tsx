import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { LedgerPage } from './LedgerPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.ledger;

describe('T08 Management table', () => {
  it("declares the plan's archetype: dense, exported in bulk, no prose regions", () => {
    expect(TEMPLATE.plan).toBe('T08');
    expect(TEMPLATE.density).toBe('dense');
    expect(TEMPLATE.primaryAction?.kind).toBe('export');
    // A table has no standing summary and no narrative, and declaring them is
    // how an admin page ends up looking like a document.
    expect(TEMPLATE.regions).not.toContain('summary');
    expect(TEMPLATE.regions).not.toContain('notes');
    expect(TEMPLATE.regions).toContain('detail');
  });

  it('renders filters, bulk actions and the row drawer', () => {
    const view = renderTemplate(
      <LedgerPage
        {...frameProps()}
        filters={<div>SAVED VIEWS</div>}
        actions={<div>SELECT 3</div>}
        detail={<div>DRAWER</div>}
      />,
    );
    expect(view.region('filters')?.textContent).toContain('SAVED VIEWS');
    expect(view.region('actions')?.textContent).toContain('SELECT 3');
    expect(view.region('detail')?.textContent).toContain('DRAWER');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(
      renderAllStates((state) => (
        <LedgerPage {...frameProps({ state })} filters={<div>VIEWS</div>} />
      )),
    );
  });

  it('keeps the saved views and the source on a failure', () => {
    const view = renderTemplate(
      <LedgerPage {...frameProps({ state: 'error', ok: false })} filters={<div>VIEWS</div>} />,
    );
    expect(view.region('filters')).not.toBeNull();
    expect(view.region('provenance')).not.toBeNull();
    expect(view.text()).toContain('ERROR');
  });

  it('puts the stamp on the data region when the rows arrived', () => {
    const view = renderTemplate(<LedgerPage {...frameProps({ state: 'ready' })} />);
    expect(view.stampIn('data')).not.toBeNull();
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<LedgerPage {...frameProps()} />).container);
  });
});
