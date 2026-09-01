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
          if (typeof id !== 'string' || !id.includes('node_modules')) return undefined;
          
          // Bulletproof Windows path normalization (no regex escape issues)
          const n = id.split('\\').join('/');
          
          // Core React & Router (Eager)
          if (n.includes('/react-dom/') || n.includes('/react/') || n.includes('/scheduler/') || n.includes('/react-router')) return 'vendor-react';
          
          // UI / Motion / Icons
          if (n.includes('/framer-motion/') || n.includes('/motion-dom/') || n.includes('/motion-utils/')) return 'vendor-motion';
          if (n.includes('/lucide-react/')) return 'vendor-icons';
          
          // Ant Design Ecosystem
          if (n.includes('/antd/') || n.includes('/@ant-design/') || n.includes('/@rc-component/') || n.includes('/rc-') || n.includes('/dayjs/') || n.includes('/stylis/')) return 'vendor-antd';
          
          // Charts & Redux (Recharts 3.x uses Redux internally)
          if (n.includes('/recharts/') || n.includes('/d3-') || n.includes('/victory-vendor/') || n.includes('/redux/') || n.includes('/@reduxjs/') || n.includes('/immer/') || n.includes('/reselect/') || n.includes('/react-redux/')) return 'vendor-charts';
          
          // 3D / Three.js Ecosystem
          if (n.includes('/three/') || n.includes('/three-stdlib/') || n.includes('/@react-three/') || n.includes('/postprocessing/') || n.includes('/n8ao/') || n.includes('/maath/') || n.includes('/suspend-react/') || n.includes('/its-fine/') || n.includes('/react-use-measure/')) return 'vendor-three';
          
          // Deck.gl / Map Ecosystem
          if (n.includes('/@deck.gl/') || n.includes('/@luma.gl/') || n.includes('/@loaders.gl/') || n.includes('/@math.gl/') || n.includes('/@probe.gl/') || n.includes('/mjolnir.js/') || n.includes('/hammerjs/')) return 'vendor-deckgl';
          
          // i18n & Query & State
          if (n.includes('/i18next/') || n.includes('/react-i18next/')) return 'vendor-i18n';
          if (n.includes('/@tanstack/')) return 'vendor-query';
          if (n.includes('/zustand/') || n.includes('/use-sync-external-store/')) return 'vendor-state';
          
          // CRITICAL: Return undefined for unmatched modules.
          // This forces Rolldown to place them in the chunks of their importers,
          // preserving laziness and completely eliminating the vendor-other catch-all!
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
