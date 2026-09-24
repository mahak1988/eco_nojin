import { test, expect } from '@playwright/test';

test.describe('Hydroma Science Page', () => {
  test('loads and displays C++ status, models list', async ({ page }) => {
    await page.goto('/fa/hydroma');
    await expect(page).toHaveTitle(/علم/);
    
    // Title
    await expect(page.locator('h1')).toContainText('علم و ابزارهای هیدروما');
    
    // C++ status
    await expect(page.locator('text=پردازش علمی فعلاً در دسترس نیست')).toBeVisible();
    
    // Models section
    await expect(page.locator('text=ابزارهای ثبت‌شده')).toBeVisible();
    await expect(page.locator('text=ابزارهای علمی')).toBeVisible();
  });

  test('English locale shows C++ status', async ({ page }) => {
    await page.goto('/en/hydroma');
    await expect(page.locator('text=The C++ numerical core is not available')).toBeVisible();
  });
});

test.describe('Hydroma - Navigation', () => {
  test('navigates from cover page', async ({ page }) => {
    await page.goto('/fa');
    await page.click('a:has-text("ورود به صفحات عمومی")');
    await page.click('a:has-text("دیدن موتور علمی هیدروما")');
    await expect(page).toHaveURL(/\/fa\/hydroma/);
  });

  test('navigates from home page', async ({ page }) => {
    await page.goto('/fa/home');
    await page.click('a:has-text("دیدن موتور علمی هیدروما")');
    await expect(page).toHaveURL(/\/fa\/hydroma/);
  });
});