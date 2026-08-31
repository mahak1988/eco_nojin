import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(import.meta.dirname, "./src"),
      },
    },
    server: {
      port: Number(env.VITE_PORT ?? 5173),
      proxy: env.VITE_DEV_PROXY
        ? {
            "/api": {
              target: env.VITE_DEV_PROXY,
              changeOrigin: true,
            },
          }
        : undefined,
    },
    build: {
      sourcemap: false,
      rollupOptions: {
        output: {
    manualChunks(id) {
      // React core
      if (id.includes('node_modules/react-dom') ||
          id.includes('node_modules/react/') ||
          id.includes('node_modules/scheduler')) {
        return 'vendor-react';
      }
      // 3D libraries
      if (id.includes('node_modules/three') ||
          id.includes('node_modules/@react-three')) {
        return 'vendor-3d';
      }
      // UI framework
      if (id.includes('node_modules/antd') ||
          id.includes('node_modules/@ant-design')) {
        return 'vendor-ui';
      }
      // Charts
      if (id.includes('node_modules/echarts') ||
          id.includes('node_modules/zrender')) {
        return 'vendor-charts';
      }
      // Maps
      if (id.includes('node_modules/maplibre-gl') ||
          id.includes('node_modules/@deck.gl')) {
        return 'vendor-maps';
      }
      return undefined;
    },
        },
      },
    },
  };
});