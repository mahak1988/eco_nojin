import type { MetadataRoute } from 'next';

import { SITE_URL as BASE } from '@/config/site';
import { locales } from '@/i18n/routing';
import { PAGE_CATALOG, PAGE_CATALOG_VERSION } from '@/lib/domains/page-catalog';

export const dynamic = 'force-static';

/**
 * Sitemap generated from the page catalogue rather than a hand-written list.
 *
 * The previous version carried nineteen hard-coded routes, cross-multiplied by
 * fourteen locales. Two problems came with that list. It drifted: adding a page
 * to the catalogue did nothing here, so 213 indexable deep paths were absent.
 * And it advertised routes the catalogue deliberately marks `noindex` — `/system`
 * is `internal`, and a sitemap is an instruction to index.
 *
 * The catalogue is the single source of truth for what exists and whether it may
 * be indexed, so this now reads `entry.indexable` and emits nothing else. Routes
 * served by the catalogue catch-all are `planned` or `unavailable` and therefore
 * `noindex`, so they are correctly absent: a sitemap entry for a page that
 * carries `robots: noindex` is a contradiction.
 *
 * `lastModified` is the catalogue version, not `new Date()`. The file is
 * `force-static`, so a build-time clock would stamp every entry with the moment
 * the build ran and tell crawlers every page had changed that instant.
 */
function changeFrequencyFor(entry: (typeof PAGE_CATALOG)[number]): 'daily' | 'weekly' | 'monthly' {
  if (entry.path === '/') return 'daily';
  if (entry.domain === 'marketplace') return 'daily';
  if (entry.domain === 'system' || entry.domain === 'admin' || entry.domain === 'workspace') {
    return 'weekly';
  }
  return 'weekly';
}

function priorityFor(entry: (typeof PAGE_CATALOG)[number]): number {
  if (entry.path === '/' || entry.path === '/home') return 1;
  if (entry.domain === 'public' || entry.domain === 'marketplace') return 0.8;
  if (entry.domain === 'learning') return 0.7;
  return 0.6;
}

/**
 * Paths a sitemap can actually list.
 *
 * The catalogue marks eleven entries `capability` and indexable, but those carry
 * a parameter — `/market/bazaars/{id}`, `/market/product/{id}` — so they describe
 * a route template, not a URL. A sitemap entry must be a real address; listing
 * the template would publish a literal `{id}` to crawlers. They stay indexable
 * through the page's own `robots` and are reached by following links, so
 * dropping them here loses nothing.
 */
function isListablePath(path: string): boolean {
  return !path.includes('{');
}

export default function sitemap(): MetadataRoute.Sitemap {
  // The catalogue root is `/`; the route the platform actually serves for it is
  // `/{locale}`. `/home` is the same surface under its declared path, so both are
  // emitted rather than letting one URL stand in for the other.
  const indexable = PAGE_CATALOG.filter((entry) => entry.indexable && isListablePath(entry.path));
  const lastModified = new Date(PAGE_CATALOG_VERSION);

  return locales.flatMap((locale) =>
    indexable.map((entry) => {
      const path = entry.path === '/' ? '' : entry.path;
      const url = `${BASE}/${locale}${path}`;
      return {
        url,
        lastModified,
        changeFrequency: changeFrequencyFor(entry),
        priority: priorityFor(entry),
        alternates: {
          languages: Object.fromEntries(
            locales.map((alt) => {
              const altPath = entry.path === '/' ? '' : entry.path;
              return [alt, `${BASE}/${alt}${altPath}`];
            }),
          ),
        },
      };
    }),
  );
}

/**
 * Cross-check used by the test: a catalogue path that is indexable and has a
 * concrete URL must appear. Exported so the test can assert both directions.
 */
export function sitemapPathSet(): Set<string> {
  return new Set(
    PAGE_CATALOG.filter((entry) => entry.indexable && isListablePath(entry.path)).map((entry) =>
      entry.path === '/' ? '/' : entry.path,
    ),
  );
}
