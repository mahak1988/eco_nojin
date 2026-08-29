import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // فقط اگر از ایمپورت‌های «@/...» استفاده می‌کنید نگه دارید
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // ws: true,  // ← اگر وب‌سوکت دارید (پنل live؟) فعال کنید
      },
    },
  },

  // پراکسی برای تست بیلد پروداکشن (npm run preview)
  preview: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },

  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          const groups: Record<string, string[]> = {
            three:  ['three', '@react-three', 'rapier3d'],
            maps:   ['maplibre-gl', 'deck.gl', '@deck.gl', '@turf', 'geotiff'],
            charts: ['echarts', 'recharts', 'd3'],
            web3:   ['ethers', 'viem', 'wagmi', '@web3modal'],
            ui:     ['@mui', '@emotion', 'antd', '@ant-design'],
          }
          for (const [chunk, pkgs] of Object.entries(groups)) {
            if (pkgs.some(p => id.includes(`node_modules/${p}`))) return chunk
          }
        },
      },
    },
  },
})