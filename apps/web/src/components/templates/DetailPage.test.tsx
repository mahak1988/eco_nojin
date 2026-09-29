import { describe, expect, it } from 'vitest';

import { TEMPLATE_BY_ID } from '@/lib/design/page-templates';

import { DetailPage } from './DetailPage';
import {
  expectFiveStates,
  expectHeadingOrder,
  frameProps,
  renderAllStates,
  renderTemplate,
} from './templateTestHarness';

const TEMPLATE = TEMPLATE_BY_ID.detail;

describe('T04 Detail', () => {
  it("declares the plan's archetype: one entity, a submit action, a summary rail", () => {
    expect(TEMPLATE.plan).toBe('T04');
    expect(TEMPLATE.density).toBe('comfortable');
    expect(TEMPLATE.primaryAction?.kind).toBe('submit');
    expect(TEMPLATE.regions).toContain('summary');
    expect(TEMPLATE.provenance.anchor).toBe('summary');
  });

  it('puts the action and the summary in a sticky rail beside the record', () => {
    const view = renderTemplate(
      <DetailPage {...frameProps()} actions={<div>BUY</div>} summary={<div>FACTS</div>} />,
    );
    const aside = view.container.querySelector('aside');
    expect(aside?.className).toContain('sticky');
    expect(aside?.textContent).toContain('BUY');
    expect(aside?.textContent).toContain('FACTS');
    expect(view.region('data')?.textContent).toContain('DATA');
  });

  it('puts the source stamp on the summary, where the numbers you act on are', () => {
    const view = renderTemplate(
      <DetailPage {...frameProps()} actions={<div>BUY</div>} summary={<div>FACTS</div>} />,
    );
    expect(view.stampIn('summary')).not.toBeNull();
    expect(view.stampIn('summary')?.getAttribute('data-provenance')).toBe('/api/v1/example');
  });

  it("renders all five of §4.5's states", () => {
    expectFiveStates(
      renderAllStates((state) => (
        <DetailPage
          {...frameProps({ state })}
          actions={<div>BUY</div>}
          summary={<div>FACTS</div>}
        />
      )),
    );
  });

  it('keeps the stamp on the summary even when the contract did not answer', () => {
    const view = renderTemplate(
      <DetailPage {...frameProps({ state: 'error', ok: false })} summary={<div>FACTS</div>} />,
    );
    expect(view.q('[data-provenance]')).not.toBeNull();
    expect(view.text()).toContain('ERROR');
  });

  it('has one h1 and no heading before it', () => {
    expectHeadingOrder(renderTemplate(<DetailPage {...frameProps()} />).container);
  });
});
