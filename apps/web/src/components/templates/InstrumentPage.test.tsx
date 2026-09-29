import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { InstrumentPage } from './InstrumentPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.instrument;

describe('T07 Scientific instrument', () => {
  it("is the archetype the plan's gap table is about, and is dense", () => {
    expect(TEMPLATE.plan).toBe('T07');
    expect(TEMPLATE.density).toBe('dense');
    expect(TEMPLATE.primaryAction?.kind).toBe('run');
    expect(TEMPLATE.regions).toContain('filters');
    expect(TEMPLATE.regions).toContain('summary');
  });

  it('puts a sticky input contract beside the output scene', () => {
    const view = renderTemplate(
      <InstrumentPage {...frameProps()} input={<form aria-label="INPUTS">FIELDS</form>} />,
    );
    const input = view.q('[data-region="instrument-input"]');
    expect(input?.textContent).toContain('FIELDS');
    expect(input?.className).toContain('sticky');
    expect(view.q('[data-region="instrument-output"]')?.textContent).toContain('DATA');
  });

  it('gives both halves a heading, in order, so the two panels are navigable', () => {
    const view = renderTemplate(<InstrumentPage {...frameProps()} input={<form>FIELDS</form>} />);
    const order = [...view.container.querySelectorAll('[data-region]')].map((node) =>
      node.getAttribute('data-region'),
    );
    expect(order.indexOf('instrument-input')).toBeGreaterThanOrEqual(0);
    expect(order.indexOf('instrument-input')).toBeLessThan(order.indexOf('instrument-output'));
    expect(view.q('#region-instrument-input')).not.toBeNull();
    expect(view.q('#region-instrument-output')).not.toBeNull();
    expect(view.container.querySelectorAll('h1')).toHaveLength(1);
  });

  it("reuses ResourcePage's render prop so a run sees the state it was given", () => {
    const seen: number[] = [];
    renderTemplate(
      <InstrumentPage {...frameProps({ total: 51 })} input={<form>FIELDS</form>}>
        {({ total, state, path }) => {
          seen.push(total);
          return <p>{`${state}:${path}`}</p>;
        }}
      </InstrumentPage>,
    );
    expect(seen).toEqual([51]);
    expect(renderTemplate(<InstrumentPage {...frameProps()} input={<i />} />).text()).toContain(
      'DATA',
    );
  });

  it("renders all five of §4.5's states, keeping the input panel on each", () => {
    const views = renderAllStates((state) => (
      <InstrumentPage {...frameProps({ state })} input={<form>FIELDS</form>} />
    ));
    expectFiveStates(views);
    for (const view of views) {
      expect(
        view.q('[data-region="instrument-input"]'),
        'a failed run keeps its inputs',
      ).not.toBeNull();
    }
  });

  it('puts the source stamp on the summary rail when one is given', () => {
    const view = renderTemplate(
      <InstrumentPage {...frameProps()} input={<form>FIELDS</form>} summary={<div>META</div>} />,
    );
    expect(view.stampIn('summary')).not.toBeNull();
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(
      renderTemplate(<InstrumentPage {...frameProps()} input={<form>FIELDS</form>} />).container,
    );
  });
});
