import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3001';

/**
 * Browser channel used by the local gate.
 *
 * `pnpm exec playwright install chromium` downloads the bundled build from
 * `cdn.playwright.dev`, which answers `403 AccessDenied — not available in your
 * location` on some networks, so the documented `pnpm test:e2e` cannot be made
 * to work by a download step alone. Windows ships a Chromium browser either way,
 * so the local gate falls back to Edge rather than failing. `PLAYWRIGHT_CHANNEL`
 * still wins, and a value of `bundled` forces the downloaded build, which is
 * what a Linux CI runner with network access to the CDN wants.
 */
const CHANNEL =
  process.env.PLAYWRIGHT_CHANNEL === 'bundled'
    ? undefined
    : (process.env.PLAYWRIGHT_CHANNEL ?? (process.platform === 'win32' ? 'msedge' : undefined));

const WEB_SERVER_COMMAND = process.env.CI
  ? 'pnpm exec next start -p 3001'
  : 'pnpm exec next dev -p 3001';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { outputFolder: 'playwright-report' }], ['list']],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], channel: CHANNEL },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: WEB_SERVER_COMMAND,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    // The BFF resolves the expected request origin from this variable and
    // throws when it is absent, so a production-mode server started without it
    // answers every mutation with a 500 instead of the intended 403. Setting it
    // here makes the test server match the documented deployment rather than
    // accidentally exercising a misconfigured one.
    env: {
      NEXT_PUBLIC_APP_URL: BASE_URL,
    },
  },
});
