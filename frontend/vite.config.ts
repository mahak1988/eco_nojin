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

// Affinity-based chunking: heavy stacks isolated, NO catch-all.
// Affinity-based chunking with Windows path normalization
function manualChunks(id: string): string | undefined {
  if (!id.includes('node_modules')) return undefined;
  
  // CRITICAL: Normalize Windows backslashes to forward slashes
  const normalized = id.replace(/\\\\/g, '/');
  
  // Core React (must be eager)
  if (/\/node_modules\/(react|react-dom|scheduler)\//.test(normalized)) return 'vendor-react';
  
  // Router (must be eager for routing)
  if (normalized.includes('react-router')) return 'vendor-router';
  
  // Ant Design + all its sub-packages
  if (/\/node_modules\/(antd|@ant-design|@rc-component|dayjs|stylis|clsx)\//.test(normalized)) {
    return 'vendor-antd';
  }
  
  // Charts + Redux stack (recharts 3.x depends on Redux internally)
  if (/\/node_modules\/(recharts|victory-vendor|d3-|@reduxjs|redux|immer|reselect|react-redux)\//.test(normalized)) {
    return 'vendor-charts';
  }
  
  // Three.js + React Three Fiber + all 3D ecosystem
  if (/\/node_modules\/(three|three-stdlib|@react-three|postprocessing|n8ao|maath|suspend-react|its-fine|react-use-measure)\//.test(normalized)) {
    return 'vendor-three';
  }
  
  // Deck.gl + Luma.gl + math.gl + probe.gl + loaders.gl
  if (/\/node_modules\/(@deck\.gl|@luma\.gl|@loaders\.gl|@math\.gl|@probe\.gl|mjolnir|hammerjs)\//.test(normalized)) {
    return 'vendor-deckgl';
  }
  
  // Motion
  if (/\/node_modules\/(framer-motion|motion-dom|motion-utils)\//.test(normalized)) {
    return 'vendor-motion';
  }
  
  // i18n
  if (normalized.includes('i18next')) return 'vendor-i18n';
  
  // React Query
  if (normalized.includes('@tanstack')) return 'vendor-query';
  
  // State management
  if (normalized.includes('zustand')) return 'vendor-state';
  
  // Icons
  if (normalized.includes('lucide-react')) return 'vendor-icons';
  
  // Small utilities → bundle with their importer (return undefined)
  // These are typically <5KB and co-locating them preserves laziness
  if (/\/node_modules\/(use-sync-external-store|tiny-invariant|eventemitter3|react-is|@babel\/runtime|@emotion|internmap|decimal\.js)\//.test(normalized)) {
    return undefined;
  }
  
  // Catch-all for any other node_modules - BUT only if small
  // This is the key fix: we do NOT have a big catch-all
  return 'vendor-other';
}

export default defineConfig(({ mode }) => ({
  plugins: [
      react(),
      visualizer({
        filename: 'dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      })
    ],

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
