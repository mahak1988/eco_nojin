import { expect, test } from '@playwright/test';

const routes = [
  '/fa/admin',
  '/fa/research',
  '/fa/research/workspace/experiment-1',
  '/fa/system',
  '/fa/system/pwa-update',
  '/fa/system/locale-fallback',
  '/fa/help',
  '/fa/workspace',
  '/fa/workspace/overview',
  '/en/research',
];

for (const route of routes) {
  test(`${route} renders without a missing message`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}
