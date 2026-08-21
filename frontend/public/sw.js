/**
 * Eco Nojin Service Worker
 *
 * Strategy: Network-first with Cache fallback
 * - Try network first
 * - If network fails, use cache
 * - Update cache on successful network fetch
 * - Enable offline functionality for remote users
 */

const CACHE_NAME = 'eco-nojin-v1.2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/pages',
  '/learn',
  '/tools',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/fonts/vazirmatn/Vazirmatn-Regular.woff2',
  '/fonts/vazirmatn/Vazirmatn-Medium.woff2',
  '/fonts/vazirmatn/Vazirmatn-Bold.woff2',
  '/fonts/vazirmatn/Vazirmatn-ExtraBold.woff2',
];

// Offline fallback for navigations (served from cache when offline)
const OFFLINE_FALLBACK = '/';

// Pre-cache static assets on install
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {
        // Graceful failure - some assets may not exist yet
        console.log('[SW] Some assets failed to cache, continuing install');
      });
    })
  );
  self.skipWaiting();
});

// Clean old caches on activate
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Network-first strategy for navigation and API
self.addEventListener('fetch', (event) => {
  const request = event.request;

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests except our API (matched by path prefix so it
  // works with any configured API_BASE host)
  if (!request.url.startsWith(self.location.origin) &&
      !request.url.includes('/api/v1/')) {
    return;
  }

  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE_NAME);

      // Network-first strategy
      try {
        const networkResponse = await fetch(request);

        // Update cache with fresh copy (only for same-origin)
        if (request.url.startsWith(self.location.origin)) {
          cache.put(request, networkResponse.clone());
        }

        return networkResponse;
      } catch (error) {
        // Network failed, try cache
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
          return cachedResponse;
        }

        // For navigation requests, return the cached index.html (SPA fallback)
        if (request.mode === 'navigate') {
          const indexCache = await cache.match('/index.html');
          if (indexCache) return indexCache;
        }

        // Final fallback
        return new Response('Offline - Eco Nojin', {
          status: 503,
          statusText: 'Service Unavailable',
          headers: { 'Content-Type': 'text/plain' },
        });
      }
    })()
  );
});

// Background sync for offline data submission
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-data') {
    event.waitUntil(syncOfflineData());
  }
});

async function syncOfflineData() {
  // Notify clients to sync their IndexedDB queue
  const clients = await self.clients.matchAll();
  clients.forEach((client) => {
    client.postMessage({ type: 'SYNC_TRIGGERED' });
  });
}

// Message handling from clients
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
