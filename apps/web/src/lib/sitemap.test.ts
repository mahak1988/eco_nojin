import { existsSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { PAGE_CATALOG, PAGE_CATALOG_TOTAL, resolveRobots } from '@/lib/domains/page-catalog';
import sitemap from '../app/sitemap';

const entries = sitemap();
const urls = new Set(entries.map((entry) => entry.url));

describe('sitemap', () => {
  it('emits every indexable catalogue path in every locale', () => {
    // Eleven `capability` entries are indexable but carry a `{param}`, so they
    // are route templates and cannot be listed as URLs.
    const indexable = PAGE_CATALOG.filter((entry) => entry.indexable && !entry.path.includes('{'));
    const localeList = new Set(
      entries.map((entry) => new URL(entry.url).pathname.split('/')[1]?.replace(/^\/+|\/+$/g, '')),
    );
    localeList.delete('');

    expect(entries).toHaveLength(indexable.length * 14);
    expect(localeList.size).toBe(14);

    for (const entry of indexable) {
      const path = entry.path === '/' ? '' : entry.path;
      for (const locale of ['fa', 'en', 'zh', 'ru', 'ur', 'ar']) {
        expect(urls.has(`https://app.eco-nojin.org/${locale}${path}`), `${locale}${path}`).toBe(
          true,
        );
      }
    }
  });

  it('never lists a route template as if it were a URL', () => {
    for (const url of urls) {
      expect(url, `sitemap URL contains a route parameter: ${url}`).not.toContain('{');
      expect(url, `sitemap URL contains a path parameter: ${url}`).not.toContain('[');
    }
  });

  it('never advertises a page the catalogue marks noindex', () => {
    // The previous hand-written list included `/system`, which the catalogue
    // marks `internal`. A sitemap entry is an instruction to index, so listing a
    // noindex route is a contradiction.
    const advertised = new Set(
      entries.map((entry) => new URL(entry.url).pathname.replace(/^\/[a-z]{2}/, '') || '/'),
    );
    const expected = new Set(
      PAGE_CATALOG.filter((entry) => entry.indexable && !entry.path.includes('{')).map((entry) =>
        entry.path === '/' ? '/' : entry.path,
      ),
    );

    // Exact set equality in both directions: nothing missing, nothing extra.
    for (const path of expected) expect(advertised.has(path), `missing ${path}`).toBe(true);
    for (const path of advertised) expect(expected.has(path), `unexpected ${path}`).toBe(true);

    const noindexPaths = PAGE_CATALOG.filter((entry) => !entry.indexable).map(
      (entry) => entry.path,
    );
    expect(noindexPaths.length).toBeGreaterThan(0);
    for (const noindexPath of noindexPaths) {
      expect(advertised.has(noindexPath), `noindex path ${noindexPath} is in the sitemap`).toBe(
        false,
      );
    }
  });

  it('keeps robots and the sitemap in agreement', () => {
    // If a page says noindex in metadata but appears in the sitemap, a crawler
    // receives two contradictory instructions. Both read the same field, and this
    // asserts the wiring rather than restating the function.
    for (const entry of PAGE_CATALOG) {
      expect(resolveRobots(entry.status).index).toBe(entry.indexable);
    }
  });

  it('carries a full hreflang block on every entry', () => {
    for (const entry of entries) {
      const languages = entry.alternates?.languages ?? {};
      expect(Object.keys(languages)).toHaveLength(14);
      for (const [locale, target] of Object.entries(languages)) {
        expect(locale).not.toBe('');
        // The catalogue root resolves to `/fa`, not `/fa/`, so the trailing slash
        // is optional.
        expect(target).toMatch(/^https:\/\/app\.eco-nojin\.org\/[a-z]{2}(\/|$)/);
      }
    }
  });

  it('stamps a stable lastModified from the catalogue version', () => {
    // `new Date()` under `force-static` would claim every page changed at the
    // moment the build ran.
    const stamps = new Set(
      entries.map((entry) =>
        entry.lastModified instanceof Date
          ? entry.lastModified.toISOString()
          : String(entry.lastModified),
      ),
    );
    expect(stamps.size).toBe(1);
    for (const entry of entries) expect(entry.lastModified).toBeInstanceOf(Date);
  });

  it('covers the catalogue rather than a hand-written list', () => {
    const indexableListable = PAGE_CATALOG.filter(
      (entry) => entry.indexable && !entry.path.includes('{'),
    ).length;
    expect(PAGE_CATALOG_TOTAL).toBe(600);
    // The old hand-written list produced 19 × 14 = 266 entries and missed every
    // deep path. These figures follow the catalogue, which follows the filesystem,
    // so they move when pages are added — deliberately, with the change recorded
    // in `page-catalog.test.ts`.
    //
    // 2026-09-29: 281 -> 294. The catalogue gained indexable surfaces
    // (`/research/hub/runs` and the registry-driven `capability` routes) without
    // this ratchet moving with it, so the sitemap was under-reporting by 13
    // paths × 14 locales. See `page-catalog.integrity.test.ts` for the status
    // totals that produced the change.
    expect(indexableListable).toBe(294);
    expect(entries.length).toBe(294 * 14);
    expect(entries.length).toBeGreaterThan(266);
  });
});

describe('catalogue reachability', () => {
  it('resolves the sitemap module from the app tree', () => {
    // Guards against the test passing in a trimmed checkout where the route file
    // the sitemap test exercises is absent.
    expect(existsSync(path.join(import.meta.dirname, '..', 'app', 'sitemap.ts'))).toBe(true);
  });
});
