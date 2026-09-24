import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

// Real backend only. No mock server, no fixtures.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  // Allow validation builds without disturbing a running `next dev` cache.
  distDir: process.env.NEXT_DIST_DIR ?? '.next',
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${apiTarget}/api/:path*` }];
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
        ],
      },
    ];
  },
};

export default withNextIntl(nextConfig);
