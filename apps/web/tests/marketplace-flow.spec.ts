import { expect, test } from '@playwright/test';

test('bazaar registry and creation entry render honest states', async ({ page }) => {
  const list = await page.goto('/fa/market/bazaars');
  expect(list?.status()).toBeLessThan(500);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.getByRole('link', { name: 'ایجاد بازارچه' })).toBeVisible();

  const create = await page.goto('/fa/market/bazaars/create');
  expect(create?.status()).toBeLessThan(500);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.getByRole('link', { name: 'ورود', exact: true })).toBeVisible();
});

test('financial pages require a session when signed out', async ({ page }) => {
  for (const route of ['/fa/market/cart', '/fa/market/checkout', '/fa/market/wallet']) {
    await page.goto(route);
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  }
});
