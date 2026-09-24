import { test, expect } from '@playwright/test';

test.describe('Market Page', () => {
  test('loads and displays stats, products with real data', async ({ page }) => {
    await page.goto('/fa/market');
    await expect(page).toHaveTitle(/بازارگاه/);
    
    // Title
    await expect(page.locator('h1')).toContainText('بازارگاه');
    
    // Stats
    await expect(page.locator('text=محصولات')).toBeVisible();
    await expect(page.locator('text=تولیدکنندگان')).toBeVisible();
    await expect(page.locator('text=ارگانیک')).toBeVisible();
    
    // Products list
    await expect(page.locator('text=گندم ارگانیک گلستان')).toBeVisible();
    await expect(page.locator('text=زعفران')).toBeVisible();
    
    // Organic badge
    await expect(page.locator('text=ارگانیک')).toBeVisible();
    
    // Prices and stock
    await expect(page.locator('text=/kg')).toBeVisible();
  });

  test('English locale shows products', async ({ page }) => {
    await page.goto('/en/market');
    await expect(page.locator('text=Organic Wheat')).toBeVisible();
    await expect(page.locator('text=Saffron')).toBeVisible();
  });

  test('product cards show price, stock, producer', async ({ page }) => {
    await page.goto('/fa/market');
    await expect(page.locator('text=رضا احمدی')).toBeVisible(); // producer
    await expect(page.locator('text=/kg')).toBeVisible();
    await expect(page.locator('text=kg')).toBeVisible(); // stock
  });
});

test.describe('Market Page - Navigation', () => {
  test('navigates from cover page', async ({ page }) => {
    await page.goto('/fa');
    await page.click('a:has-text("ورود به بازارگاه")');
    await expect(page).toHaveURL(/\/fa\/market/);
  });
});