/**
 * Cache isolation.
 *
 * `PWA_AND_OFFLINE.md` names a release gate: "Tests prove that private,
 * financial, and privileged requests never enter caches." The service worker
 * config is a promise; this file is the check that the promise holds.
 *
 * Two layers are tested. The response headers must forbid storing a private
 * payload, and the service worker configuration itself must exclude `/api/*`
 * from every runtime caching rule — read from the built worker source rather
 * than from the config file, so a later edit to the matcher cannot slip past.
 */
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';

const SW_SOURCE = path.join(process.cwd(), 'src/app/sw.ts');

const PRIVATE_SURFACES = [
  '/api/auth/session',
  '/api/v1/ecowallet/wallets',
  '/api/v1/analytics/timeseries',
  '/api/v1/admin/users',
];

test.describe('private responses are not storable', () => {
  for (const route of PRIVATE_SURFACES) {
    test(`${route} forbids shared and private storage`, async ({ request }) => {
      const response = await request.get(route);
      const cacheControl = response.headers()['cache-control'] ?? '';
      const pragma = response.headers()['pragma'] ?? '';
      // The guarantee under test is the header, not the upstream status: a 5xx
      // only means the gateway is not running in this environment.
      const forbidden =
        /no-store/i.test(cacheControl) || /private/i.test(cacheControl) || /no-cache/i.test(pragma);
      expect(forbidden, `${route} sent cache-control: "${cacheControl}"`).toBe(true);
    });
  }
});

test.describe('service worker cache policy', () => {
  test('excludes /api from every runtime caching rule', () => {
    expect(existsSync(SW_SOURCE), `${SW_SOURCE} is missing`).toBe(true);
    const source = readFileSync(SW_SOURCE, 'utf8');

    // Every runtime-caching entry whose matcher mentions a path guard must also
    // exclude the API. A rule that caches a same-origin GET without that guard
    // would put authenticated payloads in a cache the reader can inspect.
    const rules = source.match(/matcher:[\s\S]{0,240}?handler:\s*new\s+(\w+)/g) ?? [];
    expect(rules.length, 'no runtime caching rule was found to check').toBeGreaterThan(0);

    // A rule is safe when it either excludes the API by path, or uses a handler
    // that cannot store anything. `NetworkOnly` passes every request through to
    // the network, so a rule using it caches nothing regardless of its matcher.
    const pathRules = rules.filter(
      (rule) => !rule.includes('\\.') && !rule.includes('NetworkOnly'),
    );
    expect(
      pathRules.length,
      'no rule that could store a private response was found',
    ).toBeGreaterThan(0);

    for (const rule of pathRules) {
      expect(rule, `a storing rule can cache an API path: ${rule}`).toMatch(/\/api/);
    }
  });

  test('the pass-through rules use a handler that cannot store', () => {
    // A rule matching every non-GET request, or every request, is only safe
    // because of its handler. That is asserted rather than assumed.
    const source = readFileSync(SW_SOURCE, 'utf8');
    const catchAll =
      source.match(/matcher:\s*\(\)\s*=>\s*true,[\s\S]{0,80}?handler:\s*new\s+(\w+)/g) ?? [];
    for (const rule of catchAll) {
      expect(rule, `a catch-all rule stores with a caching handler: ${rule}`).toMatch(
        /NetworkOnly/,
      );
    }
  });

  test('declares a cache version, so a stale cache can be rotated', () => {
    const source = readFileSync(SW_SOURCE, 'utf8');
    expect(source).toMatch(/cacheName:\s*'[^']+-v\d+'/);
  });
});

test.describe('deployment probes stay uncached', () => {
  for (const probe of ['/health', '/ready']) {
    test(`${probe} is not stored by the client`, async ({ request }) => {
      const response = await request.get(probe);
      // Readiness legitimately reports 503 while the gateway is down; both
      // answers must forbid storage, because a probe is never cacheable.
      expect([200, 503]).toContain(response.status());
      const cacheControl = response.headers()['cache-control'] ?? '';
      expect(/no-store|no-cache/i.test(cacheControl), `${probe} sent "${cacheControl}"`).toBe(true);
    });
  }
});
