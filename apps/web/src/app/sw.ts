/// <reference lib="webworker" />

import {
  CacheFirst,
  ExpirationPlugin,
  NetworkFirst,
  NetworkOnly,
  type RuntimeCaching,
  Serwist,
  type SerwistGlobalConfig,
  StaleWhileRevalidate,
} from 'serwist';

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW: Serwist;
  }
}

declare const self: ServiceWorkerGlobalScope & {
  __SW_MANIFEST: Array<string | { url: string; revision?: string | null }>;
};

/** Font requests, by extension. Every route below matches on this. */
const FONT_FILE = /\.(?:woff2?|ttf|otf)$/i;

/**
 * Entries the font cache can hold.
 *
 * 112 is not a round number chosen to look reasonable: it is the number of
 * distinct woff2 files the stylesheets can reach — 12 in `globals.css`
 * (Vazirmatn, Markazi Text, JetBrains Mono), 3 single-slice script families
 * (`hi`, `bn`, `ur`) and the 97 `Noto Sans SC` slices. `check-font-coverage.mjs`
 * recomputes that count from the CSS and fails if the two disagree, so the
 * budget cannot quietly fall behind the font set.
 *
 * The worst case it has to survive, in the terms the budget was designed
 * against: one `zh` page touches ~20 CJK slices, a session across four `zh`
 * pages can reach 80, and a reader who ends up touching the whole family needs
 * 97. 112 covers all three, which means the cache cannot evict a slice that any
 * page can still ask for.
 *
 * Overflow, if it ever happens, is LRU: `ExpirationPlugin` expires through an
 * IndexedDB cursor ordered by last-used timestamp, oldest first, so the least
 * recently used font is dropped and refetched on next use. That is the correct
 * degradation for a bounded store — and unlike an uncapped font cache it keeps
 * a mistyped or runaway path from filling the origin's storage quota.
 */
const FONT_CACHE_MAX_ENTRIES = 112;

const runtimeCaching: RuntimeCaching[] = [
  /*
   * Fonts get their own cache and their own budget, and are matched before the
   * general static-asset route below.
   *
   * They used to share that route's `maxEntries: 80` with every js, css and
   * image on the site. A single `zh` page pulls ~20 CJK slices and the browser
   * asks for all of them in the same batch, so a session across a few `zh`
   * pages could evict the slices it had just used — a page paying for glyphs it
   * had already downloaded. One shared budget across classes with wildly
   * different request counts is the bug; a per-class budget is the fix.
   *
   * `CacheFirst`, not `StaleWhileRevalidate`: `next.config.ts` serves
   * `/fonts/:path*` with `Cache-Control: public, max-age=31536000, immutable`
   * and every filename is content-hashed, so a revalidation can only ever
   * return the identical bytes while costing a request per font per visit.
   * Serwist 9's `StaleWhileRevalidate` writes the network response back into
   * the same cache under the same key, so it would not double the entry count
   * either — it would just spend a round trip to learn nothing.
   */
  {
    matcher: ({ sameOrigin, request, url }) =>
      sameOrigin && request.method === 'GET' && FONT_FILE.test(url.pathname),
    handler: new CacheFirst({
      cacheName: 'fonts-v1',
      plugins: [
        new ExpirationPlugin({
          maxEntries: FONT_CACHE_MAX_ENTRIES,
          maxAgeSeconds: 365 * 24 * 60 * 60,
        }),
      ],
    }),
  },
  {
    // The font extensions are gone from this pattern on purpose: they are
    // budgeted above, and leaving them here would put the same file in two
    // caches with two different limits.
    matcher: /\.(?:js|css|png|jpg|jpeg|svg|webp|avif|ico)$/i,
    handler: new StaleWhileRevalidate({
      cacheName: 'static-assets-v1',
      plugins: [new ExpirationPlugin({ maxEntries: 80, maxAgeSeconds: 30 * 24 * 60 * 60 })],
    }),
  },
  {
    matcher: ({ sameOrigin, url, request }) =>
      sameOrigin && request.method === 'GET' && !url.pathname.startsWith('/api'),
    handler: new NetworkFirst({
      cacheName: 'public-pages-v1',
      networkTimeoutSeconds: 5,
      plugins: [new ExpirationPlugin({ maxEntries: 32, maxAgeSeconds: 24 * 60 * 60 })],
    }),
  },
  {
    matcher: ({ sameOrigin, url, request }) =>
      sameOrigin && request.method === 'GET' && url.pathname.startsWith('/api'),
    handler: new NetworkOnly(),
  },
  {
    matcher: ({ request }) => request.method !== 'GET',
    handler: new NetworkOnly(),
  },
  {
    matcher: () => true,
    handler: new NetworkOnly(),
  },
];

/**
 * Fonts are dropped from the precache manifest.
 *
 * `@serwist/next` builds the manifest by globbing `public/` with its default
 * pattern — every file under the directory — so all 122 woff2 files under
 * `public/fonts/` — 5.29 MB, 4.46 MB of it the `Noto Sans SC` slices — land in
 * it, and the service worker downloads every one of them on install. That is
 * the opposite of what the slicing is for: the whole point of 97 disjoint
 * `unicode-range` slices is that a page fetches the twenty its own copy touches
 * and a `de` reader fetches none, and a precache throws that away for every
 * reader in every locale.
 *
 * The real fix belongs in `next.config.ts` (`globPublicPatterns` should name
 * the asset types worth precaching instead of every file under `public/`). Until
 * that lands, this filter keeps the fonts in the runtime cache above, where the
 * budget is explicit and eviction is LRU. The four per-locale stylesheets in
 * `public/` stay precached: they are a few kilobytes, and a `zh` reader wants
 * theirs offline.
 */
const precacheEntries = self.__SW_MANIFEST.filter((entry) => {
  const url = typeof entry === 'string' ? entry : entry.url;
  return !FONT_FILE.test(url);
});

const serwist = new Serwist({
  precacheEntries,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching,
});

serwist.addEventListeners();
