import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { DiscoveryPage } from './DiscoveryPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.discovery;

describe('T03 Discovery', () => {
  it("declares the plan's archetype: compact, filter-first, filter as the action", () => {
    expect(TEMPLATE.plan).toBe('T03');
    expect(TEMPLATE.density).toBe('compact');
    expect(TEMPLATE.primaryAction?.kind).toBe('filter');
    expect(TEMPLATE.regions).toContain('filters');
    // A browsable set has no record, so it has no standing summary.
    expect(TEMPLATE.regions).not.toContain('summary');
  });

  it('sticks the filter bar, which is the whole difference from a record page', () => {
    const view = renderTemplate(
      <DiscoveryPage {...frameProps()} filters={<div>FACETS</div>} actions={<div>COMPARE</div>} />,
    );
    const filters = view.region('filters');
    expect(filters?.textContent).toContain('FACETS');
    expect(filters?.className).toContain('sticky');
    expect(view.region('actions')?.textContent).toContain('COMPARE');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(
      renderAllStates((state) => (
        <DiscoveryPage {...frameProps({ state })} filters={<div>FACETS</div>} />
      )),
    );
  });

  it('keeps the filter bar on a failure, so a reader can retry narrower', () => {
    const view = renderTemplate(
      <DiscoveryPage {...frameProps({ state: 'error', ok: false })} filters={<div>FACETS</div>} />,
    );
    expect(view.region('filters')).not.toBeNull();
    expect(view.region('provenance')).not.toBeNull();
  });

  it('puts the stamp on the data region, and names the contract when it fails', () => {
    const ready = renderTemplate(<DiscoveryPage {...frameProps({ state: 'ready' })} />);
    expect(ready.stampIn('data')).not.toBeNull();
    const failed = renderTemplate(<DiscoveryPage {...frameProps({ state: 'empty', ok: true })} />);
    expect(failed.region('provenance'), 'an empty result still names the contract').not.toBeNull();
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<DiscoveryPage {...frameProps()} />).container);
  });
});
