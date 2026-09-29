import { resolve } from 'node:path';

import { defineConfig, devices } from '@playwright/test';

/**
 * Visual regression, against the built Storybook.
 *
 * Separate from `playwright.config.ts` on purpose. That config starts Next and
 * runs the application's own e2e suite against routes; this one starts a
 * forty-line static file server over `storybook-static/` and photographs the
 * design system. Mixing them would make every design-system capture wait on a
 * Next dev server it does not need, and would put component screenshots in the
 * same report as page journeys.
 *
 * The build is a prerequisite rather than a step here: `storybook build` is run
 * explicitly (`pnpm build-storybook` before `pnpm test:visual`) so a capture can
 * never photograph a half-written preview. `reuseExistingServer` is on for local
 * iteration and the server is a no-op cost when the build is current.
 */
const HERE = resolve(import.meta.dirname);
const APP = resolve(HERE, '..');
const PORT = Number(process.env.STORYBOOK_STATIC_PORT ?? 6007);
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: resolve(HERE, 'specs'),
  outputDir: resolve(HERE, 'test-results'),
  snapshotDir: resolve(HERE, '__screenshots__'),
  // Flat, so the baseline directory reads as the list of components rather than
  // as a tree of directories that mostly contain one file.
  snapshotPathTemplate: '{snapshotDir}/{arg}{ext}',
  globalSetup: resolve(HERE, 'global-setup.ts'),
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['github'], ['list']] : [['list']],
  use: {
    baseURL: BASE_URL,
    // Every capture is the same viewport, so a height change in a component is a
    // diff rather than a crop. Storybook's own chrome is not in the frame: the
    // screenshots are of the story canvas, taken inside `iframe.html`.
    viewport: { width: 1000, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
    reducedMotion: 'reduce',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // The same fallback as `playwright.config.ts`: a Linux CI runner sets
        // PLAYWRIGHT_CHANNEL=bundled, a Windows workstation uses the installed
        // Edge, because the bundled Chromium CDN answers 403 on some networks.
        channel:
          process.env.PLAYWRIGHT_CHANNEL === 'bundled'
            ? undefined
            : (process.env.PLAYWRIGHT_CHANNEL ??
              (process.platform === 'win32' ? 'msedge' : undefined)),
      },
    },
  ],
  webServer: {
    command: `node ${resolve(APP, 'visual', 'serve-static.mjs')} ${resolve(APP, 'storybook-static')} ${PORT}`,
    url: `${BASE_URL}/index.json`,
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
});
