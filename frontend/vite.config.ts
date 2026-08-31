/**
 * Vite Configuration - ECharts Optimized
 * ========================================
 * Splits echarts into sub-chunks for better loading:
 * - vendor-echarts-core: Core functionality (~200KB)
 * - vendor-echarts-charts: Chart types (~400KB)
 * - vendor-echarts-components: UI components (~300KB)
 * - vendor-echarts-renderers: Canvas/SVG renderers (~200KB)
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

            // Ant Design Ecosystem
            if (id.includes('/antd/') ||
                id.includes('/@ant-design/') ||
                id.includes('/@rc-component/') ||
                id.includes('/rc-')) {
              return 'vendor-antd';
            }

            // Charts - Recharts
            if (id.includes('/recharts/')) return 'vendor-charts';

            // Charts - ECharts (SPLIT INTO SUB-CHUNKS)
            if (id.includes('/echarts/') || id.includes('/zrender/')) {
              // Core: Essential functionality
              if (id.includes('/core/') ||
                  id.includes('/util/') ||
                  id.includes('/model/') ||
                  id.includes('/coord/')) {
                return 'vendor-echarts-core';
              }
              // Charts: Different chart types
              if (id.includes('/chart/')) {
                return 'vendor-echarts-charts';
              }
              // Components: UI components (tooltip, legend, etc.)
              if (id.includes('/component/') ||
                  id.includes('/label/') ||
                  id.includes('/visual/')) {
                return 'vendor-echarts-components';
              }
              // Renderers: Canvas/SVG rendering
              if (id.includes('/canvas/') ||
                  id.includes('/svg/') ||
                  id.includes('/zrender/')) {
                return 'vendor-echarts-renderers';
              }
              // Fallback
              return 'vendor-echarts-core';
            }

            // 3D - Three.js
            if (id.includes('/three/') ||
                id.includes('/@react-three/')) {
              return 'vendor-three';
            }

            // Maps - Deck.gl + Luma.gl
            if (id.includes('/@deck.gl/') ||
                id.includes('/@luma.gl/') ||
                id.includes('/@loaders.gl/') ||
                id.includes('/@math.gl/')) {
              return 'vendor-deckgl';
            }

            // Maps - Leaflet
            if (id.includes('/leaflet/') ||
                id.includes('/react-leaflet/')) {
              return 'vendor-maps';
            }

            // Data Processing
            if (id.includes('/apache-arrow/') ||
                id.includes('/flatbuffers/')) {
              return 'vendor-data';
            }

            // i18n
            if (id.includes('/i18next/') ||
                id.includes('/react-i18next/')) {
              return 'vendor-i18n';
            }

            // React Query
            if (id.includes('/@tanstack/react-query/') ||
                id.includes('/@tanstack/query-core/')) {
              return 'vendor-query';
            }

            // Forms
            if (id.includes('/react-hook-form/') ||
                id.includes('/zod/') ||
                id.includes('/@hookform/')) {
              return 'vendor-forms';
            }

            // Date
            if (id.includes('/date-fns/') ||
                id.includes('/moment/')) {
              return 'vendor-date';
            }

            // State Management
            if (id.includes('/zustand/') ||
                id.includes('/immer/')) {
              return 'vendor-state';
            }

            // Utilities
            if (id.includes('/lodash/') ||
                id.includes('/axios/') ||
                id.includes('/es-toolkit/')) {
              return 'vendor-utils';
            }

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
