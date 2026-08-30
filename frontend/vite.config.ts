import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
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
          manualChunks: {
            react: ["react", "react-dom"],
            antd: ["antd"],
            three: ["three", "@react-three/fiber", "@react-three/drei"],
            deck: ["@deck.gl/core", "@deck.gl/layers", "@deck.gl/react"],
            maplibre: ["maplibre-gl"],
            charts: ["echarts"],
          },
        },
      },
    },
  };
});