import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

import {
  CATALOG_ACCESSES,
  CATALOG_DOMAINS,
  CATALOG_GROUPS,
  catalogByDomain,
  catalogFallbackPaths,
  getCatalogEntry,
  getCatalogEntryForSlug,
  isReservedPath,
  OUT_OF_CATALOGUE_ROUTES,
  PAGE_CATALOG,
  PAGE_CATALOG_TOTAL,
  PAGE_CATALOG_VERSION,
  resolveCatalogStatus,
  resolveIndexable,
  resolveRobots,
} from './page-catalog';

const WEB_ROOT = path.resolve(import.meta.dirname, '..', '..', '..');
const APP_ROOT = path.join(WEB_ROOT, 'src', 'app');
const REPO_ROOT = path.resolve(WEB_ROOT, '..', '..');

/** Real `page.tsx` routes, read from disk rather than trusted from the catalog. */
function scanRouteFiles(dir: string, acc: string[] = []): string[] {
  for (const item of readdirSync(dir, { withFileTypes: true })) {
    // `_`-prefixed folders are Next.js private folders and never route. The
    // route-handler exemption is scoped to the app root on purpose: a product
    // directory may legitimately be called `api` (`developers/api`), and a
    // name-only match silently dropped it from every coverage count.
    if (item.name.startsWith('_')) continue;
    if (item.name === 'api' && dir === APP_ROOT) continue;
    const full = path.join(dir, item.name);
    if (item.isDirectory()) {
      scanRouteFiles(full, acc);
    } else if (item.name === 'page.tsx') {
      acc.push(path.relative(REPO_ROOT, full).split(path.sep).join('/'));
    }
  }
  return acc;
}

const LOCALE_DIR = path.join(APP_ROOT, '[locale]');
const REAL_ROUTE_FILES = scanRouteFiles(LOCALE_DIR).filter(
  (file) => !file.includes('/(catalog)/') && !file.endsWith('/_not-found/page.tsx'),
);

function routeFileToLogical(file: string): string {
  const rel = file.replace('apps/web/src/app/[locale]', '').replace('/page.tsx', '');
  return (rel.replace(/\[\.\.\.(\w+)\]/g, '{*$1}').replace(/\[(\w+)\]/g, '{$1}') || '/') as string;
}

const REAL_ROUTE_PATHS = new Set(REAL_ROUTE_FILES.map(routeFileToLogical));

/** A dynamic route pattern, compiled so a concrete path can be tested against it. */
function patternToRegExp(logical: string): RegExp {
  const source = logical
    .split('/')
    .map((segment) => {
      if (segment.startsWith('{*')) return '.+';
      if (segment.startsWith('{')) return '[^/]+';
      return segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    })
    .join('/');
  return new RegExp(`^${source}/?$`);
}

const REAL_ROUTE_PATTERNS = REAL_ROUTE_FILES.map((file) => ({
  file,
  matcher: patternToRegExp(routeFileToLogical(file)),
}));

describe('page catalog registry', () => {
  it('registers exactly 600 unique paths and ids', () => {
    expect(PAGE_CATALOG_VERSION).toBe('2026-09-26');
    expect(PAGE_CATALOG_TOTAL).toBe(600);
    expect(PAGE_CATALOG).toHaveLength(600);

    const paths = new Set(PAGE_CATALOG.map((entry) => entry.path));
    const ids = new Set(PAGE_CATALOG.map((entry) => entry.id));
    expect(paths.size).toBe(600);
    expect(ids.size).toBe(600);
  });

  it('reports the derived status distribution, not the seed literal', () => {
    // `CatalogSeed.status` is documentation of intent and `buildEntry` never
    // reads it. The reported status comes from `resolveCatalogStatus`, so it is
    // the distribution that has to be pinned: a dashboard reading the seed
    // literals instead would get 132/59/255/154, and every non-`unavailable`
    // figure in that set is wrong.
    //
    // This ratchet has moved three times, and only one direction is legitimate.
    //
    //   2026-09-26, first lock: live 202 / capability 11 / planned 233. The first
    //   draft of this test asserted 206/7 from a line-by-line reading of `SEEDS`
    //   and the suite caught the 202/11 the code actually produces; the code is
    //   the authority, so the constant moved to it.
    //
    //   2026-09-26, second lock, same day: 135 pages were generated from
    //   catalogue entries that had a real gateway contract and no page. planned
    //   233 -> 118, live 202 -> 281, indexable 213 -> 328.
    //
    //   2026-09-26, third lock, same day: `routeFile` stopped being a literal
    //   and is now resolved from the filesystem inside `buildEntry`, so the
    //   catalogue cannot drift from the app tree. Capability fell 47 -> 40 and
    //   planned rose 118 -> 125, because seven parameterised pages the generator
    //   had written were removed: five would have swallowed a catalogue path that
    //   only the catch-all serves, and two declare a route parameter named
    //   `locale`, which collides with the i18n segment. Those pages are reported
    //   by `scripts/generate-resource-pages.mjs` rather than quietly absent.
    //
    //   2026-09-29, fourth lock: the `/research/hub/runs` page arrived in the
    //   tree, so that entry now resolves `live` instead of `planned`: live
    //   281 -> 282, planned 125 -> 124, indexable 333 -> 334, route 395 -> 396,
    //   catalog-catchall 176 -> 175. A page addition, not a code change.
    //
    // If a change here moves `planned` *up* or `live` *down*, a page was deleted
    // or a contract was withdrawn, and that needs a reason in this comment.
    const counts = { live: 0, capability: 0, static: 0, planned: 0, unavailable: 0 };
    for (const entry of PAGE_CATALOG) counts[entry.status] += 1;

    expect(counts).toEqual({
      live: 282,
      capability: 40,
      static: 12,
      planned: 124,
      unavailable: 142,
    });
    expect(PAGE_CATALOG.filter((entry) => entry.indexable)).toHaveLength(334);
    expect(PAGE_CATALOG.filter((entry) => entry.renderedBy === 'route')).toHaveLength(396);
    expect(PAGE_CATALOG.filter((entry) => entry.renderedBy === 'catalog-catchall')).toHaveLength(
      175,
    );
    expect(
      PAGE_CATALOG.filter((entry) => entry.renderedBy === 'marketplace-catchall'),
    ).toHaveLength(29);
  });

  it('derives the status from the inputs that decide it, for every combination', () => {
    // The four rows below are the whole of `resolveCatalogStatus`. A change to
    // the rule must be a deliberate edit here.
    const cases: Array<[Parameters<typeof resolveCatalogStatus>[0], string]> = [
      [{ endpoint: null, hasRoute: false, registryDriven: false }, 'unavailable'],
      [{ endpoint: null, hasRoute: true, registryDriven: false }, 'unavailable'],
      [{ endpoint: null, hasRoute: true, registryDriven: true }, 'unavailable'],
      [{ endpoint: null, hasRoute: true, registryDriven: false, declaredContent: true }, 'static'],
      [
        { endpoint: null, hasRoute: false, registryDriven: false, declaredContent: true },
        'unavailable',
      ],
      [{ endpoint: '/x', hasRoute: false, registryDriven: false }, 'planned'],
      [{ endpoint: '/x', hasRoute: false, registryDriven: true }, 'planned'],
      [{ endpoint: '/x', hasRoute: true, registryDriven: false }, 'live'],
      [{ endpoint: '/x', hasRoute: true, registryDriven: true }, 'capability'],
    ];
    for (const [input, expected] of cases) {
      expect(resolveCatalogStatus(input)).toBe(expected);
    }
  });

  it('spreads the catalog over the nine deterministic groups', () => {
    expect([...CATALOG_DOMAINS]).toEqual([
      'public',
      'marketplace',
      'hydroma',
      'admin',
      'research',
      'system',
      'workspace',
      'inclusive',
      'learning',
    ]);
    expect(CATALOG_GROUPS.map((group) => group.domain)).toEqual([...CATALOG_DOMAINS]);

    for (const domain of CATALOG_DOMAINS) {
      const entries = catalogByDomain(domain);
      expect(entries.length).toBeGreaterThan(0);
      expect(entries.every((entry) => entry.domain === domain)).toBe(true);
    }

    const total = CATALOG_DOMAINS.reduce((sum, domain) => sum + catalogByDomain(domain).length, 0);
    expect(total).toBe(600);
  });

  it('gives every entry the full record and a real source of truth', () => {
    for (const entry of PAGE_CATALOG) {
      expect(entry.path.startsWith('/')).toBe(true);
      expect(entry.id.startsWith(`${entry.domain}-`)).toBe(true);
      expect(entry.owner.length).toBeGreaterThan(0);
      expect(entry.gate.length).toBeGreaterThan(0);
      expect(CATALOG_ACCESSES).toContain(entry.access);
      expect(entry.description.length).toBeGreaterThan(0);
      expect(entry.description).toContain(entry.sourceOfTruth);
      expect(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']).toContain(entry.method);
      if (entry.endpoint !== null) {
        expect(entry.endpoint).toMatch(/^\/(api|analyses|dashboard)/);
      }
    }
  });

  it('only points at a source file that exists or that a registry declares', () => {
    // The scientific tool registry names the engine module behind every tool.
    // Three of those modules are declared but absent from the tree, so the
    // catalog mirrors the registry rather than inventing a different file.
    const registry = readFileSync(
      path.join(WEB_ROOT, 'src', 'lib', 'domains', 'registry.ts'),
      'utf8',
    );
    const declared = new Set(registry.match(/sourceOfTruth: '([^']+)'/g) ?? []);
    const declaredPaths = new Set(
      [...declared].map((line) => line.replace("sourceOfTruth: '", '').replace("'", '')),
    );

    for (const entry of PAGE_CATALOG) {
      const onDisk = existsSync(path.join(REPO_ROOT, entry.sourceOfTruth));
      expect(onDisk || declaredPaths.has(entry.sourceOfTruth)).toBe(true);
    }

    const missingEngineModules = PAGE_CATALOG.filter(
      (entry) =>
        entry.sourceOfTruth.startsWith('engine/') &&
        !existsSync(path.join(REPO_ROOT, entry.sourceOfTruth)),
    );
    // The three fallback modules that were the known gap now exist in the tree
    // (added 2026-09-28), so the expectation is empty. The assertion stays: if
    // one disappears again, this list stops being empty and fails loudly.
    expect(missingEngineModules.map((entry) => entry.sourceOfTruth).sort()).toEqual([]);
  });

  it('resolves status with the single published rule', () => {
    expect(resolveCatalogStatus({ endpoint: null, hasRoute: true, registryDriven: false })).toBe(
      'unavailable',
    );
    expect(resolveCatalogStatus({ endpoint: null, hasRoute: true, registryDriven: true })).toBe(
      'unavailable',
    );
    expect(
      resolveCatalogStatus({
        endpoint: '/api/v1/platform/health',
        hasRoute: false,
        registryDriven: false,
      }),
    ).toBe('planned');
    expect(
      resolveCatalogStatus({
        endpoint: '/api/v1/platform/health',
        hasRoute: true,
        registryDriven: false,
      }),
    ).toBe('live');
    expect(
      resolveCatalogStatus({
        endpoint: '/api/v1/platform/health',
        hasRoute: true,
        registryDriven: true,
      }),
    ).toBe('capability');

    for (const entry of PAGE_CATALOG) {
      expect(entry.status).toBe(
        resolveCatalogStatus({
          endpoint: entry.endpoint,
          hasRoute: entry.routeFile !== null,
          registryDriven: entry.path.includes('{'),
          declaredContent: entry.status === 'static',
        }),
      );
      expect(entry.indexable).toBe(resolveIndexable(entry.status));
    }
  });

  it('keeps every contract-less surface unavailable and noindex', () => {
    const contractLess = PAGE_CATALOG.filter(
      (entry) => entry.endpoint === null && entry.status !== 'static',
    );
    expect(contractLess.length).toBeGreaterThan(0);
    for (const entry of contractLess) {
      expect(entry.status).toBe('unavailable');
      expect(entry.indexable).toBe(false);
      expect(resolveRobots(entry.status)).toEqual({ index: false, follow: false });
    }

    // A surface with a published contract but no route yet is planned, also noindex.
    for (const entry of PAGE_CATALOG.filter((candidate) => candidate.status === 'planned')) {
      expect(entry.endpoint).not.toBeNull();
      expect(entry.routeFile).toBeNull();
      expect(resolveRobots(entry.status)).toEqual({ index: false, follow: false });
    }

    // Only a real route backed by a contract is indexable.
    for (const entry of PAGE_CATALOG.filter((candidate) => candidate.indexable)) {
      expect(['live', 'capability', 'static']).toContain(entry.status);
      expect(entry.routeFile).not.toBeNull();
      if (entry.status !== 'static') expect(entry.endpoint).not.toBeNull();
      expect(resolveRobots(entry.status)).toEqual({ index: true, follow: true });
    }

    expect(PAGE_CATALOG.some((entry) => entry.status === 'live')).toBe(true);
    expect(PAGE_CATALOG.some((entry) => entry.status === 'capability')).toBe(true);
    expect(PAGE_CATALOG.some((entry) => entry.status === 'planned')).toBe(true);
    expect(PAGE_CATALOG.some((entry) => entry.status === 'unavailable')).toBe(true);
  });

  it('never claims an endpoint the gateway does not publish', () => {
    const openapi = JSON.parse(readFileSync(path.join(REPO_ROOT, 'openapi.json'), 'utf8')) as {
      paths: Record<string, unknown>;
    };
    const published = Object.keys(openapi.paths).map((entry) => entry.replace(/\/$/, ''));

    for (const entry of PAGE_CATALOG) {
      if (entry.endpoint === null) continue;
      const isPublished = published.some(
        (candidate) => candidate === entry.endpoint || candidate.startsWith(`${entry.endpoint}/`),
      );
      expect(isPublished, `unpublished endpoint on ${entry.path}: ${entry.endpoint}`).toBe(true);
    }
  });

  it('gives every live entry a route file that actually exists and matches', () => {
    for (const entry of PAGE_CATALOG) {
      if (entry.routeFile === null) continue;
      expect(existsSync(path.join(REPO_ROOT, entry.routeFile))).toBe(true);
      const owner = REAL_ROUTE_FILES.find((file) => file === entry.routeFile);
      expect(owner, `routeFile not in the real route scan: ${entry.routeFile}`).toBeDefined();
      expect(patternToRegExp(routeFileToLogical(owner as string)).test(entry.path)).toBe(true);
    }
  });
});

describe('page catalog reserved paths', () => {
  it('renders a fallback page only for surfaces no route owns', () => {
    const fallback = catalogFallbackPaths();
    expect(fallback.length).toBeGreaterThan(0);
    expect(new Set(fallback).size).toBe(fallback.length);

    for (const path of fallback) {
      // 1. no real route serves the path, so the catalog never duplicates a page
      const clash = REAL_ROUTE_PATTERNS.filter((route) => route.matcher.test(path));
      expect(clash).toEqual([]);
      // 2. no catalogue entry claims the same path twice
      expect(getCatalogEntry(path)?.path).toBe(path);
      // 3. the reserved marketplace namespace is left to its own catch-all
      expect(isReservedPath(path)).toBe(false);
    }
  });

  it('leaves the marketplace namespace to the existing marketplace catch-all', () => {
    expect(isReservedPath('/market')).toBe(true);
    expect(isReservedPath('/market/categories/discover-1')).toBe(true);
    expect(isReservedPath('/marketplace')).toBe(false);
    expect(isReservedPath('/system/market')).toBe(false);

    for (const entry of PAGE_CATALOG.filter((candidate) => candidate.routeFile === null)) {
      if (isReservedPath(entry.path)) {
        expect(entry.renderedBy).toBe('marketplace-catchall');
      } else {
        expect(entry.renderedBy).toBe('catalog-catchall');
      }
    }
  });

  it('inventories the fallback set without claiming a prerendered page', () => {
    // These surfaces are all `planned` or `unavailable`, therefore noindex, and
    // the catch-all renders them on demand. The inventory exists so a test can
    // prove none of them is shadowed by a real page; it is not a build list.
    const fallback = catalogFallbackPaths();
    expect(new Set(fallback).size).toBe(fallback.length);
    expect(fallback.every((path) => path.startsWith('/'))).toBe(true);
    expect(fallback.every((path) => !path.includes('//'))).toBe(true);

    // A dynamic catalog path has no single address to enumerate, so it is served
    // on demand and is listed without being claimed as a concrete instance.
    const dynamic = fallback.filter((path) => path.includes('{'));
    expect(dynamic.length).toBeGreaterThan(0);
    for (const path of dynamic) {
      expect(getCatalogEntry(path)?.renderedBy).toBe('catalog-catchall');
    }
  });

  it('resolves a known path and rejects an unknown one', () => {
    expect(getCatalogEntry('/')?.path).toBe('/');
    expect(getCatalogEntry('/nope/never-registered')).toBeUndefined();
    expect(getCatalogEntryForSlug([])?.path).toBe('/');
    expect(REAL_ROUTE_PATHS.size).toBeGreaterThan(100);
  });
});

/**
 * R-3: every physical route is either claimed by a catalog entry or declared
 * out of catalogue with a reason. The check runs in both directions so neither
 * side can drift: a new page without a catalog entry fails, and a declaration
 * that is no longer needed fails.
 */
describe('physical route coverage', () => {
  const uncatalogued = REAL_ROUTE_FILES.filter(
    (file) =>
      !PAGE_CATALOG.some((entry) => patternToRegExp(routeFileToLogical(file)).test(entry.path)),
  ).sort();
  const declared = OUT_OF_CATALOGUE_ROUTES.map((route) => route.routeFile).sort();

  it('declares exactly the routes no catalog entry claims', () => {
    expect(uncatalogued).toEqual(declared);
  });

  it('backs every declaration with a file on disk and a written reason', () => {
    for (const route of OUT_OF_CATALOGUE_ROUTES) {
      expect(existsSync(path.join(REPO_ROOT, route.routeFile))).toBe(true);
      expect(route.reason.length).toBeGreaterThan(20);
      expect(route.path.startsWith('/')).toBe(true);
      // The declaration is only honest while the path really is unclaimed.
      const owner = REAL_ROUTE_FILES.find((file) => file === route.routeFile);
      expect(owner, `declared route is not a real page: ${route.routeFile}`).toBeDefined();
      expect(
        PAGE_CATALOG.some((entry) =>
          patternToRegExp(routeFileToLogical(owner as string)).test(entry.path),
        ),
        `${route.path} is declared out of catalogue but a catalog entry claims it`,
      ).toBe(false);
    }
  });

  it('covers every physical route from the catalog or the declaration', () => {
    const covered = REAL_ROUTE_FILES.length - uncatalogued.length;
    expect(REAL_ROUTE_FILES.length).toBeGreaterThan(200);
    // The join rule the dashboard could not state: physical routes resolve to a
    // catalog path, and the residue is named rather than implied.
    expect(covered + uncatalogued.length).toBe(REAL_ROUTE_FILES.length);
    expect(uncatalogued.length).toBe(OUT_OF_CATALOGUE_ROUTES.length);
  });

  it('lets a seed override its group access when the contract disagrees', () => {
    // The `system` group is labelled `internal`, but `/dashboard/public/*` is
    // mounted without authentication, so those surfaces are public. The label
    // has to follow the contract rather than the team.
    const publicDashboards = PAGE_CATALOG.filter((entry) =>
      entry.path.startsWith('/system/dashboard/public/'),
    );
    expect(publicDashboards).toHaveLength(11);
    for (const entry of publicDashboards) {
      expect(entry.access, `${entry.path} must report the contract, not the group`).toBe('public');
    }

    // A sibling in the same group that is not overridden keeps the group value.
    const groupAccess = CATALOG_GROUPS.find((group) => group.domain === 'system')?.access;
    expect(groupAccess).toBe('internal');
    const inherited = PAGE_CATALOG.filter(
      (entry) => entry.domain === 'system' && !entry.path.startsWith('/system/dashboard/public/'),
    );
    expect(inherited.length).toBeGreaterThan(0);
    for (const entry of inherited) expect(entry.access).toBe(groupAccess);
  });
});
