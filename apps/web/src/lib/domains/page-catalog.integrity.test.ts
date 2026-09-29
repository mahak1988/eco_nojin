import { existsSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

import {
  CATALOG_STATUS_TOTALS,
  getCatalogEntry,
  OUT_OF_CATALOGUE_ROUTES,
  PAGE_CATALOG,
  PAGE_CATALOG_TOTAL,
} from './page-catalog';

/**
 * Regression guards for damage this session actually caused.
 *
 * Twice, a routine command destroyed committed-looking work:
 *
 *  1. `git checkout` on this file reverted uncommitted work that was *not* in
 *     HEAD — `OUT_OF_CATALOGUE_ROUTES` and the eleven `access` overrides on
 *     `/system/dashboard/public/*`. Both had to be rewritten by hand. The test
 *     suite did not catch it, because the importer of `OUT_OF_CATALOGUE_ROUTES`
 *     is a test file, and a missing export in a test-only helper fails late and
 *     noisily.
 *  2. The `pageMeta` applier ran its "no hand-written pair, so drop the entry"
 *     branch against `en.json` as well, deleting the reference catalogue's own
 *     305 keys.
 *
 * These assertions exist so neither can recur silently. They are cheap, and a
 * catalogue that quietly loses its inventory is worse than a build that fails.
 */
function findRepoRoot(from: string): string {
  let current = from;
  for (let depth = 0; depth < 12; depth += 1) {
    if (existsSync(path.join(current, 'scripts', 'check-locale-encoding.mjs'))) return current;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(`could not locate the repository root above ${from}`);
}

const REPO_ROOT = findRepoRoot(import.meta.dirname);

describe('page catalog integrity', () => {
  it('keeps its declared size', () => {
    // The one number everything else is measured against. If a regeneration
    // changes the catalogue deliberately, this is where the change is recorded.
    expect(PAGE_CATALOG_TOTAL).toBe(600);
    expect(PAGE_CATALOG).toHaveLength(600);
    // 2026-09-29: /research/hub/runs gained a page; live 281 -> 282, planned 125 -> 124.
    expect(CATALOG_STATUS_TOTALS).toEqual({
      live: 282,
      capability: 40,
      static: 12,
      planned: 124,
      unavailable: 142,
    });
  });

  it('keeps a unique path and id for every entry', () => {
    expect(new Set(PAGE_CATALOG.map((entry) => entry.path)).size).toBe(600);
    expect(new Set(PAGE_CATALOG.map((entry) => entry.id)).size).toBe(600);
  });

  it('declares the unclaimed routes it is supposed to declare', () => {
    // `git checkout` removed this export once. It is the only declaration of
    // which routes are deliberately outside the catalogue, and "declares exactly
    // the routes no catalog entry claims" above depends on it.
    expect(OUT_OF_CATALOGUE_ROUTES.length).toBeGreaterThanOrEqual(4);
    for (const route of OUT_OF_CATALOGUE_ROUTES) {
      expect(existsSync(path.join(REPO_ROOT, route.routeFile)), route.routeFile).toBe(true);
      expect(route.path.startsWith('/')).toBe(true);
      // A reason per entry, so the list cannot quietly become a dumping ground.
      expect(route.reason.length, route.path).toBeGreaterThan(20);
      // And the declaration is only honest while the path really is unclaimed.
      expect(getCatalogEntry(route.path), route.path).toBeUndefined();
    }
  });

  it('labels the public dashboards public, following the contract', () => {
    // The `system` group is `internal`, but `dashboard.py` mounts
    // `/dashboard/public/*` without authentication, so those eleven surfaces are
    // public. These overrides were also lost to the same `git checkout`.
    const dashboards = PAGE_CATALOG.filter((entry) =>
      entry.path.startsWith('/system/dashboard/public/'),
    );
    expect(dashboards).toHaveLength(11);
    for (const entry of dashboards) {
      expect(entry.access, entry.path).toBe('public');
    }
  });

  it('gives every entry an owner, a gate and a description', () => {
    for (const entry of PAGE_CATALOG) {
      expect(entry.owner, entry.id).toBeTruthy();
      expect(entry.gate, entry.id).toBeTruthy();
      expect(entry.description.length, entry.id).toBeGreaterThan(20);
      expect(entry.access, entry.id).toBeTruthy();
    }
  });
});
