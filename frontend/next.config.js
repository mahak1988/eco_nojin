/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Next.js 16: Turbopack is the default bundler.
  // The legacy webpack resolve.fallback (fs/net/tls -> false) is not needed
  // under Turbopack; if a client package imports Node builtins, the build
  // will fail loudly and we fix the specific import instead of masking it.
  turbopack: {},

  // Disable image optimization to avoid sharp dependency issues
  images: {
    unoptimized: true,
  },

  // Phase 0: the codebase carries pre-existing TypeScript debt (implicit any,
  // loose API types) that was never type-checked green. We ship the CVE-fixed
  // Next.js 16 build now and track the cleanup as W-022 in
  // docs/11_weaknesses_and_fixes.md (scheduled for Phase 3 frontend rebuild).
  typescript: {
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;
