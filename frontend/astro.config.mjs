import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://econojin.org',
  output: 'server',
  adapter: {
    name: 'node',
    entry: './dist/server/entry.mjs',
  },
  integrations: [
    react({
      experimental: {
        ssr: true,
      },
    }),
    tailwind({ applyBaseStyles: false }),
    sitemap({
      filter: (page) => !page.includes('/dashboard'),
    }),
    mdx(),
  ],
  vite: {
    server: {
      port: 4321,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      target: 'es2020',
      cssCodeSplit: true,
      assetsInlineLimit: 4096,
      rollupOptions: {
        output: {
          manualChunks: {
            'astro-react': ['react', 'react-dom', 'react/jsx-runtime'],
          },
        },
      },
    },
  },
  trailingSlash: 'always',
  compressHTML: true,
  prefetch: true,
});
