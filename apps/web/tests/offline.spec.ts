import { expect, test } from '@playwright/test';

test('public page remains available after the first online visit', async ({ page, context }) => {
  await page.goto('/fa/home');
  await page.evaluate(() => navigator.serviceWorker.ready.then(() => undefined));
  await page.reload();
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
  await context.setOffline(true);
  try {
    await page.reload();
    await expect(page.locator('h1').first()).toBeVisible();
  } finally {
    await context.setOffline(false);
  }
});
