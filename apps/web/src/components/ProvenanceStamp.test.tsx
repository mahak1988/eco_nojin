import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ProvenanceStamp } from './ProvenanceStamp';

afterEach(() => {
  cleanup();
});

/** Index just past the opening tag's `>`, tracking braces inside attributes. */
function openTagEnd(src: string, from: number): number {
  let depth = 0;
  for (let i = from; i < src.length; i += 1) {
    const c = src[i];
    if (c === '{') depth += 1;
    else if (c === '}') depth -= 1;
    else if (c === '>' && depth === 0) return i;
  }
  return -1;
}

function walk(dir: string, acc: string[] = []): string[] {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, acc);
    else if (entry.name.endsWith('.tsx')) acc.push(full);
  }
  return acc;
}

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

  it('renders a heading passed as a child when no label is supplied', () => {
    render(
      <ProvenanceStamp source="station:IRN-YZD-01" verified>
        <h1>Station IRN-YZD-01</h1>
      </ProvenanceStamp>,
    );

    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Station IRN-YZD-01');
  });

  /**
   * `label ?? children` means a call site that passes both renders the label and
   * silently drops the heading. Sixty-one public pages did exactly that and
   * shipped without an `h1`; this guards the whole surface against a repeat.
   */
  it('has no call site that would drop a heading behind a label', () => {
    const offenders: string[] = [];
    for (const file of walk(path.join(process.cwd(), 'src'))) {
      const src = readFileSync(file, 'utf8');
      const pattern = /<ProvenanceStamp\b/g;
      let match = pattern.exec(src);
      while (match) {
        const end = openTagEnd(src, match.index + match[0].length);
        if (end < 0) break;
        const openTag = src.slice(match.index, end + 1);
        const close = src.indexOf('</ProvenanceStamp>', end);
        if (openTag.trimEnd().endsWith('/>') || !/\blabel=/.test(openTag) || close < 0) {
          pattern.lastIndex = close < 0 ? end + 1 : close + 20;
          match = pattern.exec(src);
          continue;
        }
        if (/<h1\b/.test(src.slice(end + 1, close))) {
          offenders.push(path.relative(process.cwd(), file));
        }
        pattern.lastIndex = close + 20;
        match = pattern.exec(src);
      }
    }

    expect(offenders).toEqual([]);
  });
});
