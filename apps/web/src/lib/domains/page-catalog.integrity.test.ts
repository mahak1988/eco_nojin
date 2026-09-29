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
    expect(PAGE_CATALOG_TOTAL).toBe(621);
    expect(PAGE_CATALOG).toHaveLength(621);
    // 2026-09-29: /research/hub/runs gained a page; live 281 -> 282, planned 125 -> 124.
    //
    // 2026-09-29, second movement today: planned 124 -> 120, capability 40 -> 44.
    // Four pages were generated from the catalogue's own declared GET contracts:
    //
    //   /market/villages/{village_id}          GET  /api/v1/marketplace/villages/{village_id}
    //   /hydroma/carbon/verra/{registry_id}    GET  /api/v1/carbon/verra/{registry_id}
    //   /hydroma/carbon/{model_id}             GET  /api/v1/hydroma/carbon/{model_id}
    //   /system/iot/devices/{device_id}        GET  /api/v1/iot/devices/{device_id}
    //
    // All four are registry-driven paths, so `resolveCatalogStatus` calls them
    // `capability` rather than `live` and they are indexable. `planned` falls by
    // the same four. `PAGE_CATALOG_TOTAL` is unchanged at 600: no entry was
    // added to or removed from the catalogue, four entries stopped being
    // `planned`. See the change log in `page-catalog.test.ts` for why these four
    // were being suppressed, and `scripts/generate-resource-pages.mjs` for the
    // rule that was wrong.
    //
    // 2026-09-29, third movement: live 282 -> 283, planned 120 -> 119, and
    // `PAGE_CATALOG_TOTAL` still 600. `market/villages/b2b/demands/page.tsx`
    // arrived in the tree while the seed still said `planned`, so the entry
    // resolved `live` off the filesystem. One page, no seed edit, no contract
    // change. The ratchet had not been re-run, which is why this log exists.
    //
    // 2026-09-29, fourth movement, and the first that changes the total:
    // 600 -> 621, live 283 -> 295, capability 44 -> 53, planned unchanged at 119.
    // Twenty-one route files had been on disk with no catalogue entry, and
    // `page-catalog.test.ts` was failing on the difference in both directions.
    // They are added here rather than declared in `OUT_OF_CATALOGUE_ROUTES`,
    // which is for pages that duplicate a catalogued surface under another path:
    // each of the twenty-one is the only page for its route, and each has a
    // published `GET`. The twelve that name no parameter resolve `live` and the
    // nine that do resolve `capability`, so `planned` does not move.
    //
    // The twenty-one, by the reason the page was hand-written rather than
    // generated — the generator derives a `rowsKey` from the path, and deriving
    // one is what produced a permanent empty state over a 200 in 24 places:
    //
    //   six `_SPECS` families   rows key is `models`, not the leaf
    //   hydroma/models          the payload is a bare list[ModelMeta]
    //   validation/run          a command, not a listing
    //   market/orders/…/transitions   a bare list[str]
    //
    // Twelve hydroma, one marketplace listing, one marketplace record and one
    // marketplace list. Their contracts are `hydroma_indices.py`, `hydroma_mrv.py`,
    // `hydroma_simulation.py`, `hydroma_soil.py`, `hydroma_water.py`,
    // `hydroma_dashboard.py`, `hydroma_ops.py`, `services/validation/router.py`
    // and `services/commerce/routers/commerce.py`; the three validation sub-paths
    // are declared by a router mounted at `services/api_gateway/main.py:583` and
    // are absent from the committed `openapi.json`, which predates the mount.
    // `page-catalog.test.ts` therefore reads the mounted routers as well.
    //
    // Also in this change: `/hydroma/tools/mrv-nojin` no longer names
    // `engine/hydroma/mrv/nojin_mrv.py`, which is deleted in the working tree. It
    // names the surviving MRV data-model module in the same package. The deletion
    // is not this file's to undo, and pointing the entry at a module that is not
    // there would turn a missing engine file into a silent lie in the inventory.
    expect(CATALOG_STATUS_TOTALS).toEqual({
      live: 295,
      capability: 53,
      static: 12,
      planned: 119,
      unavailable: 142,
    });
  });

  it('keeps a unique path and id for every entry', () => {
    expect(new Set(PAGE_CATALOG.map((entry) => entry.path)).size).toBe(621);
    expect(new Set(PAGE_CATALOG.map((entry) => entry.id)).size).toBe(621);
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
