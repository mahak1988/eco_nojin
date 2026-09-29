import { expect, test } from '@playwright/test';

test.describe('Market Page', () => {
  test('loads and displays stats, products with real data', async ({ page }) => {
    await page.goto('/fa/market');
    await expect(page).toHaveTitle(/بازارگاه/);

    // Title
    await expect(page.locator('h1')).toContainText('بازارگاه');

    // Stats
    await expect(page.locator('text=محصولات').first()).toBeVisible();
    await expect(page.locator('text=تولیدکنندگان').first()).toBeVisible();
    await expect(page.locator('text=ارگانیک').first()).toBeVisible();

    // Product names are the canonical API values (English) until the data carries
    // localized names; the UI must not invent a translation.
    // Products list
    await expect(page.locator('text=Organic Wheat').first()).toBeVisible();
    await expect(page.locator('text=Saffron').first()).toBeVisible();

    // Organic badge
    await expect(page.locator('text=ارگانیک').first()).toBeVisible();

    // Prices and stock
    await expect(page.getByTestId('price').first()).toBeVisible();
  });

  test('English locale shows products', async ({ page }) => {
    await page.goto('/en/market');
    await expect(page.locator('text=Organic Wheat').first()).toBeVisible();
    await expect(page.locator('text=Saffron').first()).toBeVisible();
  });

  test('product cards show price, stock, producer', async ({ page }) => {
    await page.goto('/fa/market');
    await expect(page.getByTestId('producer').first()).toBeVisible(); // producer (real API value)
    await expect(page.getByTestId('price').first()).toBeVisible();
    await expect(page.getByTestId('stock').first()).toBeVisible(); // stock
  });
});

test.describe('Market Page - Navigation', () => {
  test('navigates from cover page', async ({ page }) => {
    await page.goto('/fa');
    await page.click('a:has-text("ورود به بازارگاه")');
    await expect(page).toHaveURL(/\/fa\/market/);
  });
});
