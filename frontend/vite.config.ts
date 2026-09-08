/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// Vite configuration for the Eco Nojin public website.
// Dev server on 5173, preview (production build) on 4173.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    open: false,
  },
  preview: {
    port: 4173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: false,
    setupFiles: ['src/test/setup.ts'],
  },
});
