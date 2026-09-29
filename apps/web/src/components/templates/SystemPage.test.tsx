import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { SystemPage } from './SystemPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.system;

describe('T11 System', () => {
  it("declares the plan's archetype: calm, and with nothing to explore", () => {
    expect(TEMPLATE.plan).toBe('T11');
    expect(TEMPLATE.density).toBe('comfortable');
    expect(TEMPLATE.primaryAction?.kind).toBe('navigate');
    // The point of T11 is what it leaves out: no filters, no summary, no detail.
    expect(TEMPLATE.regions).not.toContain('filters');
    expect(TEMPLATE.regions).not.toContain('summary');
    expect(TEMPLATE.regions).not.toContain('detail');
    expect(TEMPLATE.regions).toContain('actions');
  });

  it('offers a way back rather than a way forward', () => {
    const view = renderTemplate(
      <SystemPage
        {...frameProps()}
        actions={<a href="/home">BACK</a>}
        notes={<div>STILL WORKS</div>}
      />,
    );
    expect(view.region('actions')?.textContent).toContain('BACK');
    expect(view.region('notes')?.textContent).toContain('STILL WORKS');
  });

  it("renders all five of §4.5's states, and a system page is often in one", () => {
    const views = renderAllStates((state) => (
      <SystemPage {...frameProps({ state, ok: state === 'ready' })} />
    ));
    expectFiveStates(views);
    expect(views.map((view) => view.text())).toEqual([
      expect.stringContaining('LOADING'),
      expect.stringContaining('EMPTY'),
      expect.stringContaining('ERROR'),
      expect.stringContaining('PARTIAL'),
      expect.stringContaining('OFFLINE'),
    ]);
  });

  it('names the contract even when the contract is the thing that is down', () => {
    const view = renderTemplate(<SystemPage {...frameProps({ state: 'error', ok: false })} />);
    expect(view.region('provenance')).not.toBeNull();
    expect(view.q('[data-provenance]')?.getAttribute('data-provenance')).toBe('/api/v1/example');
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<SystemPage {...frameProps()} />).container);
  });
});
