import { expect, test } from '@playwright/test';

const routes = [
  '/fa/developers/api',
  '/fa/developers/status-api',
  '/fa/trust/carbon-registry',
  '/fa/trust/provenance',
  '/fa/ai/glossary',
  '/fa/ai/voice',
  '/fa/references',
  '/fa/validation',
];

for (const route of routes) {
  test(`${route} renders an honest state`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}
