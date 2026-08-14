/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Next.js 15 doesn't support allowedDevOrigins (that's Next.js 16+)
  // Instead, we'll handle CORS in the backend
  
  // Disable image optimization to avoid sharp dependency issues
  images: {
    unoptimized: true,
  },
  
  // Webpack configuration (Next.js 15 uses Webpack by default)
  webpack: (config, { isServer }) => {
    // Fix for some packages that use Node.js built-in modules
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
