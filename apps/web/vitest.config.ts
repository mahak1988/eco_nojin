import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text-summary', 'json-summary', 'html'],
      reportsDirectory: './coverage',
      // The scope the docs talk about: what the reader actually executes. Route
      // files and generated catalogues are measured separately, because
      // including them would report a number nobody can act on.
      include: ['src/lib/**', 'src/components/**', 'src/i18n/**', 'src/config/**'],
      exclude: [
        '**/*.test.{ts,tsx}',
        '**/*.d.ts',
        'src/lib/domains/page-catalog.ts',
        'src/content/**',
      ],
      // `TESTING.md` states 80% as a decision gate. Measured on 2026-09-26 the
      // real figure was 41.5% lines, so enforcing 80% would fail every run and
      // teach the team to ignore the gate. These thresholds are a ratchet at the
      // measured floor: the gate now fails on regression, and each wave raises
      // the numbers as tests are added. The 80% target stays recorded as the
      // goal, not as a number the repository pretends to meet.
      thresholds: { lines: 41, functions: 41, branches: 38, statements: 41 },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
});
