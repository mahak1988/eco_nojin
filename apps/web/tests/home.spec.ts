import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('loads and displays live stats, land profiles, and products', async ({ page }) => {
    await page.goto('/fa/home');
    await expect(page).toHaveTitle(/هیدروما نوژین/);
    
    // Title
    await expect(page.locator('h1')).toContainText('هیدروما نوژین — پلتفرم احیای مَنظر');
    
    // Stats cards (live data)
    await expect(page.locator('text=زمین‌های ثبت‌شده')).toBeVisible();
    await expect(page.locator('text=پروژه‌های کربن')).toBeVisible();
    await expect(page.locator('text=محصولات بازارگاه')).toBeVisible();
    
    // Real data indicator
    await expect(page.locator('text=وضعیت ثبت‌شدهٔ سامانه')).toBeVisible();
    
    // Land profiles list
    await expect(page.locator('text=مزرعه گندم ارگانیک گلستان')).toBeVisible();
    
    // Products
    await expect(page.locator('text=زعفران')).toBeVisible();
    
    // CTAs
    await expect(page.locator('a:has-text("مشاهدهٔ بازارگاه")')).toBeVisible();
    await expect(page.locator('a:has-text("دیدن موتور علمی هیدروما")')).toBeVisible();
  });

  test('English locale shows real data', async ({ page }) => {
    await page.goto('/en/home');
    await expect(page.locator('text=Land profiles')).toBeVisible();
    await expect(page.locator('text=Organic Wheat')).toBeVisible();
  });

  test('navigates to market from CTA', async ({ page }) => {
    await page.goto('/fa/home');
    await page.click('a:has-text("مشاهدهٔ بازارگاه")');
    await expect(page).toHaveURL(/\/fa\/market/);
  });

  test('navigates to hydroma from CTA', async ({ page }) => {
    await page.goto('/fa/home');
    await page.click('a:has-text("دیدن موتور علمی هیدروما")');
    await expect(page).toHaveURL(/\/fa\/hydroma/);
  });
});

test.describe('Home Page - RTL/LTR', () => {
  test('fa and ar are RTL', async ({ page }) => {
    await page.goto('/fa/home');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    
    await page.goto('/ar/home');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
  });

  test('en and de are LTR', async ({ page }) => {
    await page.goto('/en/home');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
    
    await page.goto('/de/home');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
  });
});