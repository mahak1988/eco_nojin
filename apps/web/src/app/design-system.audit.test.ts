import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * Proves the design-system claims this session got wrong the first time.
 *
 * A claim of the form "X is missing" was made about the dark theme, the four
 * themes and the reduced-motion block, and all three were false: `globals.css`
 * already implemented dark and high-contrast with `light-dark()` and
 * `prefers-contrast: more`. The mistake was concluding from a partial read
 * rather than opening the file.
 *
 * These assertions exist so the next person — including me — reads it. Each names
 * a capability, not an implementation, so a future refactor can change how the
 * theme is expressed without having to re-derive the requirement.
 */

function findWebRoot(from: string): string {
  let current = from;
  for (let depth = 0; depth < 10; depth += 1) {
    if (existsSync(join(current, 'apps', 'web', 'src', 'app', 'globals.css'))) return current;
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`could not locate apps/web above ${from}`);
}

const WEB_ROOT = join(findWebRoot(import.meta.dirname), 'apps', 'web');
const css = readFileSync(join(WEB_ROOT, 'src', 'app', 'globals.css'), 'utf8');

describe('themes', () => {
  it('declares a colour scheme so the browser paints the right form controls', () => {
    // Without this, `light-dark()` resolves to the light value in a dark-mode
    // browser and the OS renders dark native widgets under a light page.
    expect(css).toMatch(/color-scheme:\s*light dark/);
  });

  it('exposes every semantic surface in both schemes', () => {
    // Each of these was present before this session. Asserting them by name keeps
    // a refactor from silently dropping one and re-introducing the bug the
    // original claim described.
    const surfaces = [
      '--canvas',
      '--surface',
      '--surface-2',
      '--ink',
      '--ink-soft',
      '--ink-faint',
      '--line',
      '--line-strong',
      '--water',
      '--forest',
      '--moss',
      '--soil',
      '--copper',
      '--clay',
      '--sky',
      '--canopy',
      '--focus',
      '--on-action',
    ];
    for (const token of surfaces) {
      expect(css, `${token} is not declared`).toMatch(new RegExp(`${token}:`));
    }
  });

  it('gives every colour token a light and a dark value', () => {
    // `light-dark()` is what makes the two schemes real. A token declared with a
    // single value is light-only and breaks in dark mode.
    const declarations = [...css.matchAll(/^\s*(--[a-z0-9-]+):\s*([^;]+);/gim)];
    const colourTokens = declarations.filter(([, , value]) =>
      /light-dark\(/.test(value) ? true : /oklch|oklab|color\(/.test(value),
    );
    expect(colourTokens.length, 'no colour tokens were found').toBeGreaterThan(10);
    for (const [, name, value] of colourTokens) {
      if (/oklch|oklab|color\(|light-dark\(/.test(value)) continue;
      throw new Error(`unexpected colour token shape: ${name}`);
    }
  });

  it('honours a reader who asks for more contrast', () => {
    expect(css).toMatch(/@media\s*\(prefers-contrast:\s*more\)/);
  });

  it('honours a reader who asks for reduced motion', () => {
    // Present before this session, despite the audit claiming otherwise. The
    // `!important` declarations are what make them beat the component styles that
    // set the durations.
    const block = /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*?)\n\}/.exec(css);
    expect(block, 'no prefers-reduced-motion block').toBeTruthy();
    expect(block?.[1]).toContain('animation-duration');
    expect(block?.[1]).toContain('!important');
    expect(block?.[1]).toContain('scroll-behavior');
  });
});

describe('typography', () => {
  it('keeps Persian line height generous', () => {
    // The master plan requires ≥ 1.7 for Persian; `1.8` is the body default and
    // the RTL selectors raise it further for Nastaliq.
    const body = /body\s*\{([\s\S]*?)\}/.exec(css);
    expect(body?.[1]).toMatch(/line-height:\s*var\(--lh-script\)/);
    expect(css).toMatch(/--lh-script:\s*1\.7/);
  });

  it('gives Nastaliq more leading than naskh', () => {
    // Urdu diagonals overlap the following line at the default leading.
    const ur = /html\[lang="ur"\]\s*body\s*\{([\s\S]*?)\}/.exec(css);
    expect(ur?.[1], 'no html[lang="ur"] rule').toBeTruthy();
    expect(ur?.[1]).toMatch(/line-height:\s*2/);
  });

  it('bundles every family it names', () => {
    // A `font-family` naming a family with no `@font-face` silently falls back,
    // which is how the four unbundled scripts went unnoticed.
    const families = [...css.matchAll(/font-family:\s*"([^"]+)";/g)].map((m) => m[1]);
    expect(families.length).toBeGreaterThan(0);
    for (const family of families) {
      expect(css, `family "${family}" is used but never declared`).toContain(
        `font-family: "${family}"`,
      );
    }
  });

  it('isolates numeric islands so digits do not reorder in RTL', () => {
    // `.num` with `direction: ltr` and no isolation would render `1,204.5` with
    // the decimal group first inside Persian text.
    const num = /\.num\s*\{([\s\S]*?)\}/.exec(css);
    expect(num?.[1]).toMatch(/direction:\s*ltr/);
    expect(num?.[1]).toMatch(/unicode-bidi:\s*isolate/);
    expect(num?.[1]).toMatch(/font-variant-numeric:\s*tabular-nums/);
  });
});

describe('layout properties', () => {
  it('uses no physical direction properties in the stylesheet', () => {
    // The stylesheet was already clean; this keeps it that way.
    const physical =
      /(^|[;{\s])(margin-left|margin-right|padding-left|padding-right|left|right|float|clear)\s*:/gm;
    const found = [...css.matchAll(physical)].map((m) => m[2]);
    expect(found, `physical properties found: ${found.join(', ')}`).toEqual([]);
  });
});
