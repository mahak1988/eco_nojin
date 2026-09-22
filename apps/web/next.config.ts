import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

// Real backend only. No mock server, no fixtures.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${apiTarget}/api/:path*` }];
  },
};

export default withNextIntl(nextConfig);
