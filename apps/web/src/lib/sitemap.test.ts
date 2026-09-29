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
    expect(PAGE_CATALOG_TOTAL).toBe(621);
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
    //
    // 2026-09-29: unchanged at 294, and the reason is the point. Four more
    // catalogue entries became indexable the same day — capability 40 -> 44,
    // indexable 334 -> 338 — but all four are parameterised
    // (`/market/villages/{village_id}`, `/hydroma/carbon/verra/{registry_id}`,
    // `/hydroma/carbon/{model_id}`, `/system/iot/devices/{device_id}`), and a
    // sitemap entry has to be a real address. Listing `/market/villages/{id}`
    // would publish a literal `{village_id}` to crawlers, which is the same
    // defect the `isListablePath` filter exists to prevent. The count is the
    // count of listable paths, and four route templates are not listable.
    // 2026-09-29: 294 -> 295. One catalogue entry gained a page on disk while its
    // seed still said `planned` — `/market/villages/b2b/demands` — so it resolved
    // `live` and became listable. The ratchet had not been re-run. See the change
    // log in `page-catalog.integrity.test.ts`.
    //
    // 2026-09-29: 295 -> 307. The catalogue grew by twenty-one entries, of which
    // twelve are listable. The nine that carry a `{param}` are the same case the
    // paragraph above already states: `/hydroma/indices/{model_id}`,
    // `/hydroma/models/{model_id}`, `/hydroma/models/{model_id}/validation`,
    // `/hydroma/mrv/{model_id}`, `/hydroma/simulation/{model_id}`,
    // `/hydroma/soil/{model_id}`, `/hydroma/water/{model_id}`, `/market/orders/{id}`
    // and `/market/orders/{id}/transitions` are route templates, not addresses, and
    // publishing a literal brace to a crawler is the defect `isListablePath` exists
    // to prevent. The twelve listable are the eleven hydroma surfaces (`indices`,
    // `models`, `mrv`, `simulation`, `slaughterhouse/status`, `soil`, `validation`,
    // `validation/checks`, `validation/reference-data`, `validation/run`, `water`)
    // plus `/market/escrow/orders`.
    //
    // One caveat, recorded rather than hidden: `/market/escrow/orders` sets
    // `robots: { index: false, follow: true }` in its own `generateMetadata`, and
    // the catalogue's single rule resolves it `live`, so it is listed here. The
    // catalogue has no status that means "renders a contract but must not be
    // indexed" — `indexable` is derived, and the only way to switch it off is to
    // deny that a contract exists. Fixing it properly means either the page
    // dropping its own `robots` or the status model gaining a `live + noindex`
    // state; neither is in this file's ownership, and neither is invented here.
    expect(indexableListable).toBe(307);
    expect(entries.length).toBe(307 * 14);
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
