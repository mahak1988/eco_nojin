import { describe, expect, it } from 'vitest';

import type { DataState } from '@/components/ui/StateSlot';
import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { CoverPage } from './CoverPage';
import {
  ALL_STATES,
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.cover;

describe('T01 Cover', () => {
  it("declares the plan's archetype: hero layout, comfortable, anchored on the data", () => {
    expect(TEMPLATE.plan).toBe('T01');
    expect(TEMPLATE.name).toBe('Cover');
    expect(TEMPLATE.density).toBe('comfortable');
    expect(TEMPLATE.provenance.anchor).toBe('data');
    expect(TEMPLATE.primaryAction?.kind).toBe('navigate');
  });

  it('renders the plan id and density on the page, for the gate to read', () => {
    const view = renderTemplate(<CoverPage {...frameProps()} actions={<a href="/market">GO</a>} />);
    expect(view.q('[data-page-template]')?.getAttribute('data-page-template')).toBe('T01');
    expect(view.q('[data-density]')?.getAttribute('data-density')).toBe('comfortable');
    expect(view.region('actions')).not.toBeNull();
    expect(view.text()).toContain('GO');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(renderAllStates((state) => <CoverPage {...frameProps({ state })} />));
  });

  it('shows the state copy, not a fabricated zero', () => {
    const copy: Partial<Record<DataState, string>> = {
      loading: 'LOADING',
      empty: 'EMPTY',
      error: 'ERROR',
      partial: 'PARTIAL',
      offline: 'OFFLINE',
    };
    for (const state of ALL_STATES) {
      const view = renderTemplate(<CoverPage {...frameProps({ state })} />);
      expect(view.text(), `${state} copy`).toContain(copy[state]);
    }
  });

  it('puts the source stamp on the data region when there is data', () => {
    const view = renderTemplate(<CoverPage {...frameProps({ state: 'ready' })} />);
    expect(view.stampIn('data')).not.toBeNull();
    expect(view.stampIn('data')?.getAttribute('data-provenance')).toBe('/api/v1/example');
  });

  it('keeps the source stamp on the page when the contract did not answer', () => {
    const view = renderTemplate(<CoverPage {...frameProps({ state: 'error', ok: false })} />);
    expect(view.region('provenance'), 'a failed page still names its contract').not.toBeNull();
    expect(view.q('[data-provenance]')).not.toBeNull();
    expect(view.text()).toContain('UNAVAILABLE');
  });

  it('has one h1 and no heading before it', () => {
    const view = renderTemplate(<CoverPage {...frameProps()} />);
    expectHeadingOrder(view.container);
  });
});
