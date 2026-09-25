/// <reference lib="webworker" />

import {
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

const runtimeCaching: RuntimeCaching[] = [
  {
    matcher: /\.(?:js|css|woff2?|ttf|png|jpg|jpeg|svg|webp|avif|ico)$/i,
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

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching,
});

serwist.addEventListeners();
