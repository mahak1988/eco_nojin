/**
 * Sponsor slot placement guard.
 *
 * Mirrors `FORBIDDEN_PLACEMENT_PREFIXES` in
 * `services/sponsors/policy.py`. Two sides of the same rule is a risk, so this
 * test proves the two lists still agree: change one without the other and the
 * build fails.
 *
 * It walks the whole route tree, so a slot added to a protected page later is
 * caught even though nobody remembers this test exists. It is a static file
 * scan and needs no browser, which is why it is a vitest unit test rather than
 * a Playwright spec.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

// apps/web/src/lib -> apps/web/src/lib/../../../.. == repo root
const REPO = join(__dirname, '..', '..', '..', '..');
const APP_DIR = join(REPO, 'apps', 'web', 'src', 'app');
const COMPONENT = join(REPO, 'apps', 'web', 'src', 'components', 'SponsorSlot.tsx');
const POLICY = join(REPO, 'services', 'sponsors', 'policy.py');
const MODEL = join(REPO, 'services', 'sponsors', 'models', '__init__.py');

/** Must match FORBIDDEN_PLACEMENT_PREFIXES in policy.py. */
const FORBIDDEN = [
  '/hydroma',
  '/virtual-lab',
  '/simulator',
  '/simulators',
  '/models',
  '/advisor',
  '/checkout',
  '/wallet',
  '/escrow',
  '/orders',
  '/settings',
  '/profile',
  '/admin',
  '/telecom',
  '/ussd',
  '/voice',
  '/simple',
  '/offline',
];

const ALLOWED_PLACEMENTS = ['public_services', 'public_audiences', 'tool_footer'];

function walk(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) walk(full, out);
    else if (entry.endsWith('.tsx')) out.push(full);
  }
  return out;
}

function routeOf(file: string): string {
  const rel = relative(APP_DIR, file).replace(/\\/g, '/');
  const stripped = rel.replace(/^\[locale\]\/?/, '').replace(/^app\//, '');
  const cut = stripped.indexOf('/');
  const route = cut === -1 ? `/${stripped}` : `/${stripped.slice(0, cut)}`;
  return route.replace(/\/page\.tsx$/, '').replace(/\/+$/, '') || '/';
}

function isBlocked(route: string): boolean {
  const clean = route.replace(/\/+$/, '') || '/';
  return FORBIDDEN.some((p) => clean === p || clean.startsWith(`${p}/`));
}

describe('sponsor slot placement', () => {
  const files = walk(APP_DIR);

  it('found the route tree', () => {
    expect(files.length).toBeGreaterThan(50);
  });

  it('no protected route mounts SponsorSlot', () => {
    const violations: string[] = [];
    for (const file of files) {
      if (!readFileSync(file, 'utf8').includes('SponsorSlot')) continue;
      const route = routeOf(file);
      if (isBlocked(route)) violations.push(route);
    }
    expect(violations).toEqual([]);
  });

  it('every mount site passes an allowed placement', () => {
    const bad: string[] = [];
    for (const file of files) {
      const src = readFileSync(file, 'utf8');
      if (!src.includes('<SponsorSlot')) continue;
      const ok = ALLOWED_PLACEMENTS.some(
        (p) => src.includes(`placement="${p}"`) || src.includes(`placement={'${p}'}`),
      );
      if (!ok) bad.push(routeOf(file));
    }
    expect(bad).toEqual([]);
  });

  it('no mount site passes a forbidden placement literal', () => {
    const bad: string[] = [];
    for (const file of files) {
      const src = readFileSync(file, 'utf8');
      if (!src.includes('<SponsorSlot')) continue;
      for (const p of FORBIDDEN) {
        if (src.includes(`placement="${p}"`)) bad.push(`${routeOf(file)}:${p}`);
      }
    }
    expect(bad).toEqual([]);
  });

  it('the slot is actually installed somewhere, or this suite is vacuous', () => {
    const mounted = files.filter((f) => readFileSync(f, 'utf8').includes('<SponsorSlot'));
    expect(mounted.length).toBeGreaterThan(0);
  });
});

describe('the component holds the behavioural rules', () => {
  it('marks the link as sponsored', () => {
    expect(readFileSync(COMPONENT, 'utf8')).toContain('rel="sponsored');
  });

  it('contains no tracking of any kind', () => {
    const src = readFileSync(COMPONENT, 'utf8');
    for (const forbidden of [
      'gtag',
      'googletagmanager',
      'fbq',
      'dataLayer',
      'navigator.sendBeacon',
      'IntersectionObserver',
      'document.cookie',
      'localStorage',
    ]) {
      expect(src).not.toContain(forbidden);
    }
  });

  it('renders nothing rather than an empty frame when absent', () => {
    const src = readFileSync(COMPONENT, 'utf8');
    expect(src).toContain('if (!data?.present) return null;');
  });

  it('the disclosure element cannot be hidden or removed', () => {
    const src = readFileSync(COMPONENT, 'utf8');
    expect(src).toContain('data-testid="sponsor-disclosure"');
    const after = src.slice(src.indexOf('data-testid="sponsor-disclosure"'));
    expect(after).not.toContain('hidden');
    expect(after).not.toContain('opacity-0');
  });

  it('has a fixed width so it cannot shift layout', () => {
    expect(readFileSync(COMPONENT, 'utf8')).toContain('max-w-[240px]');
  });
});

describe('the two sides of the policy agree', () => {
  const policySrc = readFileSync(POLICY, 'utf8');

  it('policy.py declares exactly these prefixes', () => {
    const block = policySrc.slice(
      policySrc.indexOf('FORBIDDEN_PLACEMENT_PREFIXES'),
      policySrc.indexOf('FORBIDDEN_PLACEMENTS:'),
    );
    const declared = [...block.matchAll(/^\s*"([^"]+)"/gm)].map((m) => m[1]);
    expect(declared.sort()).toEqual([...FORBIDDEN].sort());
  });

  it('policy.py declares the same visual budget the component respects', () => {
    expect(policySrc).toContain('MAX_VISUAL_WEIGHT_PCT = 12');
    expect(policySrc).toContain('MAX_SPONSORS_PER_PLACEMENT = 1');
  });

  it('the model has no impression field', () => {
    // Engagement is never recorded, so it can never be reported to a sponsor
    // or optimised for one. Scan the column declarations only: the docstrings
    // deliberately *mention* these words to explain their absence.
    const model = readFileSync(MODEL, 'utf8');
    const columns = [...model.matchAll(/^\s{4}(\w+)\s*=\s*Column\(/gm)].map((m) => m[1]);
    expect(columns.length).toBeGreaterThan(10);
    for (const forbidden of [
      'impressions',
      'impression_count',
      'view_count',
      'views',
      'click_count',
      'clicks',
      'reach',
    ]) {
      expect(columns).not.toContain(forbidden);
    }
  });
});
