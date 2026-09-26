import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

import {
  CATALOG_ACCESSES,
  CATALOG_DOMAINS,
  CATALOG_GROUPS,
  catalogByDomain,
  catalogFallbackParams,
  catalogFallbackPaths,
  getCatalogEntry,
  getCatalogEntryForSlug,
  isReservedPath,
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
    if (item.name.startsWith('_') || item.name === 'api') continue;
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
    // Known gap in the existing scientific tool registry, surfaced not hidden.
    expect(missingEngineModules.map((entry) => entry.sourceOfTruth).sort()).toEqual([
      'engine/hydroma/cpp_bridge/hydrology_fallback.py',
      'engine/hydroma/cpp_bridge/indices_fallback.py',
      'engine/hydroma/cpp_bridge/soil_physics_fallback.py',
    ]);
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
        }),
      );
      expect(entry.indexable).toBe(resolveIndexable(entry.status));
    }
  });

  it('keeps every contract-less surface unavailable and noindex', () => {
    const contractLess = PAGE_CATALOG.filter((entry) => entry.endpoint === null);
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
      expect(['live', 'capability']).toContain(entry.status);
      expect(entry.routeFile).not.toBeNull();
      expect(entry.endpoint).not.toBeNull();
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

  it('builds one unique static param per fallback path', () => {
    const params = catalogFallbackParams();
    const keys = params.map((param) => param.slug.join('/'));
    // A dynamic catalog path has no single instance to prerender, so it is
    // served on demand and never enters the static param list.
    const staticPaths = catalogFallbackPaths().filter((path) => !path.includes('{'));

    expect(params).toHaveLength(staticPaths.length);
    expect(params.length).toBeGreaterThan(0);
    expect(new Set(keys).size).toBe(params.length);
    expect(params.every((param) => param.slug.length > 0)).toBe(true);
    expect(params.every((param) => !param.slug.some((segment) => segment.includes('{')))).toBe(
      true,
    );
    expect(getCatalogEntryForSlug(['definitely', 'not', 'registered'])).toBeUndefined();
    expect(getCatalogEntryForSlug(params[0].slug)?.path).toBe(`/${params[0].slug.join('/')}`);
  });

  it('resolves a known path and rejects an unknown one', () => {
    expect(getCatalogEntry('/')?.path).toBe('/');
    expect(getCatalogEntry('/nope/never-registered')).toBeUndefined();
    expect(getCatalogEntryForSlug([])?.path).toBe('/');
    expect(REAL_ROUTE_PATHS.size).toBeGreaterThan(100);
  });
});
