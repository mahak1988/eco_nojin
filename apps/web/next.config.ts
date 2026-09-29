import withSerwistInit from '@serwist/next';
import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');
const withSerwist = withSerwistInit({
  swSrc: 'src/app/sw.ts',
  swDest: 'public/sw.js',
  disable: process.env.NODE_ENV !== 'production',
  register: true,
  reloadOnOnline: true,
  /**
   * The 122 woff2 files in `public/fonts/` must not be in the precache
   * manifest.
   *
   * `@serwist/next` defaults to a glob of every file under public, which puts
   * each one into the install-time manifest. Replaying that default
   * against this repository gives 138 entries and 11,902,467 bytes — of which
   * the 122 font files are 5,292,880 bytes. Every reader in every locale would
   * download 5.29 MB of fonts at install, and 4.46 MB of that is the CJK
   * `unicode-range` slices, which exist precisely so a reader downloads only
   * the slices their characters touch. Ten of the fourteen locales need none of
   * them at all.
   *
   * The fonts are served at runtime instead, by the `fonts-v1` `CacheFirst`
   * route in `src/app/sw.ts` with a 112-entry LRU budget sized against the
   * number of faces the stylesheets can actually reach. A reader who never opens
   * a `zh` page never fetches a single CJK slice, which is the whole point of
   * slicing them.
   *
   * This was found by measurement, not by reading the docs: the same
   * `globPublicPatterns` default was reported as "excludes woff2" in a review of
   * this file, and replaying the actual call showed otherwise.
   */
  globPublicPatterns: ['**/*', '!**/*.woff2'],
});

const nextConfig: NextConfig = {
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
  env: {
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL ?? 'https://app.eco-nojin.org',
  },
  async headers() {
    return [
      {
        source: '/fonts/:path*',
        headers: [{ key: 'Cache-Control', value: 'public, max-age=31536000, immutable' }],
      },
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'X-DNS-Prefetch-Control', value: 'on' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(self)' },
          { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
          { key: 'Cross-Origin-Resource-Policy', value: 'same-site' },
          {
            key: 'Content-Security-Policy-Report-Only',
            value:
              "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https: wss:; worker-src 'self' blob:; manifest-src 'self'; upgrade-insecure-requests; report-uri /api/csp-report",
          },
          ...(process.env.NODE_ENV === 'production'
            ? [{ key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' }]
            : []),
        ],
      },
    ];
  },
};

export default withNextIntl(withSerwist(nextConfig));
