/**
 * Vite Configuration - Vite 8 + Rolldown (No esbuild)
 * ====================================================
 * Uses Rolldown's built-in minifier instead of esbuild.
 *
 * Vite 8 Notes:
 * - Rolldown has its own high-performance minifier
 * - No external esbuild dependency needed
 * - manualChunks as function (Rolldown requirement)
 * - import.meta.dirname instead of __dirname
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    mode === 'analyze' &&
      visualizer({
        open: true,
        filename: 'dist/stats.html',
        gzipSize: true,
        brotliSize: true,
      }),
  ].filter(Boolean),

  resolve: {
    alias: {
      '@': import.meta.dirname + '/src',
      '@features': import.meta.dirname + '/src/features',
      '@components': import.meta.dirname + '/src/components',
      '@hooks': import.meta.dirname + '/src/hooks',
      '@utils': import.meta.dirname + '/src/utils',
      '@types': import.meta.dirname + '/src/types',
    },
  },

  build: {
    target: 'es2020',
    // Rolldown's built-in minifier (no esbuild needed)
    // Setting to 'terser' would require installing terser
    // Leaving unset uses Rolldown's fast native minifier
    sourcemap: mode === 'development',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (typeof id !== 'string') return undefined;

          if (id.includes('node_modules')) {
            if (id.includes('/react-dom/') ||
                id.includes('/react/') ||
                id.includes('/react-router')) {
              return 'vendor-react';
            }
            if (id.includes('/framer-motion/') ||
                id.includes('/lucide-react/') ||
                id.includes('/@radix-ui/')) {
              return 'vendor-ui';
            }
            if (id.includes('/recharts/')) return 'vendor-charts';
            if (id.includes('/three/') ||
                id.includes('/@react-three/')) {
              return 'vendor-3d';
            }
            if (id.includes('/leaflet/') ||
                id.includes('/react-leaflet/')) {
              return 'vendor-maps';
            }
            if (id.includes('/i18next/') ||
                id.includes('/react-i18next/')) {
              return 'vendor-i18n';
            }
            if (id.includes('/@tanstack/react-query/')) {
              return 'vendor-query';
            }
            return 'vendor-other';
          }
          return undefined;
        },
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
      },
    },
    chunkSizeWarningLimit: 500,
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'framer-motion',
      'lucide-react',
    ],
  },

  server: {
    port: 5173,
    open: false,
    cors: true,
  },
}));
