import { defineConfig, devices } from '@playwright/test';

// Detect if we should use system Chrome
const useSystemChrome = process.env.PLAYWRIGHT_USE_SYSTEM_CHROME !== 'false';

export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    // Disable video/trace/screenshot to avoid ffmpeg download requirement
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
