import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { NarrativePage } from './NarrativePage';
import {
  ALL_STATES,
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.narrative;

describe('T02 Narrative', () => {
  it("declares the plan's archetype: a reading column with no action at all", () => {
    expect(TEMPLATE.plan).toBe('T02');
    expect(TEMPLATE.density).toBe('comfortable');
    expect(TEMPLATE.provenance.anchor).toBe('data');
    // The one archetype in the system with nothing to click.
    expect(TEMPLATE.primaryAction).toBeNull();
    expect(TEMPLATE.regions).not.toContain('actions');
  });

  it('offers no action region, so a reading page cannot grow a competing button', () => {
    const view = renderTemplate(<NarrativePage {...frameProps()} actions={<a href="/x">GO</a>} />);
    expect(view.region('actions')).toBeNull();
    expect(view.text()).not.toContain('GO');
  });

  it('renders the edge contents, notes and print regions it declares', () => {
    const view = renderTemplate(
      <NarrativePage
        {...frameProps()}
        detail={<nav>CONTENTS</nav>}
        notes={<p>CAVEAT</p>}
        print={<p>PRINT</p>}
      />,
    );
    expect(view.region('detail')?.textContent).toContain('CONTENTS');
    expect(view.region('notes')?.textContent).toContain('CAVEAT');
    expect(view.region('print')?.textContent).toContain('PRINT');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(renderAllStates((state) => <NarrativePage {...frameProps({ state })} />));
  });

  it('names the contract on every state', () => {
    for (const state of ALL_STATES) {
      const view = renderTemplate(
        <NarrativePage {...frameProps({ state, ok: state === 'ready' })} />,
      );
      expect(view.q('[data-provenance]'), `${state} has no source stamp`).not.toBeNull();
    }
  });

  it('puts the stamp on the data region when there is data', () => {
    const view = renderTemplate(<NarrativePage {...frameProps({ state: 'ready' })} />);
    expect(view.stampIn('data')).not.toBeNull();
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<NarrativePage {...frameProps()} />).container);
  });
});
