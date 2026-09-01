import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e/tests',
  // Serial execution to prevent race conditions
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  // CRITICAL: Add retries to handle flaky ENOENT errors
  retries: process.env.CI ? 2 : 5,
  reporter: [
    ['list'],
  ],
  timeout: 60000,
  use: {
    baseURL: 'http://localhost:5173',
    // All artifacts disabled
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    launchOptions: {
      channel: 'chrome',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
  },
  projects: [
    {
      name: 'chromium',
      use: {
        channel: 'chrome',
        ...devices['Desktop Chrome'],
      },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 180000,
  },
});
