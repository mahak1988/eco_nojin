import { expect, test } from '@playwright/test';

test.describe('marketplace core safety', () => {
  test('planned marketplace route exposes an explicit unavailable state', async ({ page }) => {
    await page.goto('/fa/market/finance/ledger-01');

    await expect(page.getByText('دادهٔ این قابلیت هنوز متصل نیست')).toBeVisible();
    await expect(page.getByText('در دسترس‌نبودن داده')).toBeVisible();
  });

  test('escrow demo does not claim a successful financial transition', async ({ page }) => {
    await page.goto('/fa/market/escrow/ESC-001');

    await expect(page.getByText('دادهٔ زندهٔ escrow در دسترس نیست')).toBeVisible();
    await expect(page.getByText('قرارداد و شرایط اسکرو')).toBeHidden();
  });
});
