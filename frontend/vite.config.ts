/**
 * Vite Configuration - Enhanced Chunk Splitting
 * ================================================
 * Splits vendor-other into smaller, more specific chunks.
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
    sourcemap: mode === 'development',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (typeof id !== 'string') return undefined;

          if (id.includes('node_modules')) {
            // Core React
            if (id.includes('/react-dom/') ||
                id.includes('/react/') ||
                id.includes('/react-router')) {
              return 'vendor-react';
            }

            // UI Libraries
            if (id.includes('/framer-motion/')) return 'vendor-motion';
            if (id.includes('/lucide-react/')) return 'vendor-icons';
            if (id.includes('/@radix-ui/')) return 'vendor-radix';

            // Charts
            if (id.includes('/recharts/')) return 'vendor-charts';
            if (id.includes('/d3-')) return 'vendor-charts';

            // 3D (very heavy)
            if (id.includes('/three/')) return 'vendor-three';
            if (id.includes('/@react-three/fiber/')) return 'vendor-three';
            if (id.includes('/@react-three/drei/')) return 'vendor-three';
            if (id.includes('/@react-three/postprocessing/')) return 'vendor-three';

            // Maps
            if (id.includes('/leaflet/')) return 'vendor-maps';
            if (id.includes('/react-leaflet/')) return 'vendor-maps';

            // i18n
            if (id.includes('/i18next/')) return 'vendor-i18n';
            if (id.includes('/react-i18next/')) return 'vendor-i18n';

            // React Query
            if (id.includes('/@tanstack/react-query/')) return 'vendor-query';
            if (id.includes('/@tanstack/query-core/')) return 'vendor-query';

            // Forms
            if (id.includes('/react-hook-form/')) return 'vendor-forms';
            if (id.includes('/zod/')) return 'vendor-forms';
            if (id.includes('/@hookform/')) return 'vendor-forms';

            // Date
            if (id.includes('/date-fns/')) return 'vendor-date';
            if (id.includes('/moment/')) return 'vendor-date';

            // Utilities
            if (id.includes('/lodash/')) return 'vendor-utils';
            if (id.includes('/axios/')) return 'vendor-utils';

            // Other vendors
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
