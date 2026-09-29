import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { LegalPage } from './LegalPage';
import {
  ALL_STATES,
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.legal;

describe('T09 Legal document', () => {
  it("declares the plan's archetype: a document with a print region and no action", () => {
    expect(TEMPLATE.plan).toBe('T09');
    expect(TEMPLATE.primaryAction).toBeNull();
    expect(TEMPLATE.regions).toContain('print');
    expect(TEMPLATE.regions).not.toContain('actions');
  });

  it('is a different archetype from T02, not T02 with a flag', () => {
    const narrative = TEMPLATE_BY_ID.narrative;
    // Same density and anchor, different intent: clauses and versions, not prose.
    expect(TEMPLATE.provenance.anchor).toBe(narrative.provenance.anchor);
    expect(TEMPLATE.regions).toContain('print');
    expect(narrative.regions).toContain('print');
    expect(TEMPLATE.intent).not.toBe(narrative.intent);
  });

  it('renders the version diff, the print masthead and the notes', () => {
    const view = renderTemplate(
      <LegalPage
        {...frameProps()}
        detail={<div>DIFF v3 → v4</div>}
        print={<div>VERSION 4</div>}
        notes={<div>JURISDICTION</div>}
      />,
    );
    expect(view.region('detail')?.textContent).toContain('DIFF v3');
    expect(view.region('print')?.textContent).toContain('VERSION 4');
    expect(view.region('notes')?.textContent).toContain('JURISDICTION');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(
      renderAllStates((state) => <LegalPage {...frameProps({ state })} print={<div>V4</div>} />),
    );
  });

  it('names the contract on every state, including a missing one', () => {
    for (const state of ALL_STATES) {
      const view = renderTemplate(<LegalPage {...frameProps({ state, ok: state === 'ready' })} />);
      expect(view.q('[data-provenance]'), `${state} has no source`).not.toBeNull();
    }
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<LegalPage {...frameProps()} />).container);
  });
});
