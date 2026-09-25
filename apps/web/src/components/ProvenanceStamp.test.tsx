import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ProvenanceStamp } from './ProvenanceStamp';

afterEach(() => {
  cleanup();
});

describe('ProvenanceStamp — Living Terrain §5.2', () => {
  it('exposes the source on the chip and on the keyboard-focusable trigger', () => {
    render(<ProvenanceStamp source="station:IRN-YZD-01">live</ProvenanceStamp>);

    const chip = document.querySelector('[data-provenance="station:IRN-YZD-01"]');
    expect(chip).not.toBeNull();
    expect(screen.getByRole('button', { name: 'station:IRN-YZD-01' })).not.toBeNull();
    expect(screen.getByText('live')).not.toBeNull();
  });

  it('renders the popover tooltip with method, confidence and observed time', () => {
    render(
      <ProvenanceStamp
        source="model-run:latest"
        verified
        method="FAO-56"
        modelConfidence={0.82}
        timestamp="2026-09-22T08:30:00.000Z"
      />,
    );

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.textContent).toContain('model-run:latest');
    expect(tooltip.textContent).toContain('FAO-56');
    expect(tooltip.textContent).toContain('82%');
    expect(screen.getByRole('img', { name: 'verified' })).not.toBeNull();
  });

  it('stays locale-neutral when no labels are supplied (no hard-coded copy)', () => {
    render(<ProvenanceStamp source="escrow-ledger" verified={false} />);

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.textContent).toContain('escrow-ledger');
    expect(tooltip.textContent).not.toMatch(/verified|source|method|confidence/i);
    expect(screen.getByRole('img', { name: 'unverified' })).not.toBeNull();
  });

  it('renders caller-provided localized labels when available', () => {
    render(
      <ProvenanceStamp
        source="station:IRN-YZD-01"
        method="FAO-56"
        labels={{
          heading: 'مُهر منشأ داده',
          source: 'منبع',
          method: 'روش',
          verified: 'تأییدشده',
        }}
        verified
      />,
    );

    const tooltip = screen.getByRole('tooltip');
    expect(tooltip.textContent).toContain('مُهر منشأ داده');
    expect(tooltip.textContent).toContain('منبع');
    expect(tooltip.textContent).toContain('روش');
    expect(screen.getByRole('img', { name: 'تأییدشده' })).not.toBeNull();
  });
});
