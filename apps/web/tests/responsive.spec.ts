import { expect, test } from '@playwright/test';

const routes = [
  '/fa/hydroma',
  '/en/home',
  '/fa/research',
  '/fa',
  '/fa/system',
  '/fa/help',
  '/fa/workspace',
  '/fa/admin',
];

for (const route of routes) {
  test(`${route} reflows at 320px`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 800 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto(route);
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => ({
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    }));
    expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth);
  });
}
