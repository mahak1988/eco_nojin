import { test, expect } from '@playwright/test';

test.describe('Cover Page (T01)', () => {
  test('loads and displays brand, subtitle, slogan, quote, and two CTAs', async ({ page }) => {
    await page.goto('/fa');
    await expect(page).toHaveTitle(/هیدروما نوژین/);
    
    // Brand name
    await expect(page.locator('header >> text=هیدروما نوژین')).toBeVisible();
    
    // Subtitle
    await expect(page.locator('text=مدیریت هوشمند مَنظر برای احیای آب، خاک و معیشت')).toBeVisible();
    
    // Slogan
    await expect(page.locator('text=ما با هم این راه را می‌رویم. برای مردم. برای زمین. برای آینده.')).toBeVisible();
    
    // Quote
    await expect(page.locator('text=این پروژه را ما با هم ساختیم')).toBeVisible();
    
    // Two CTA buttons
    await expect(page.locator('a:has-text("ورود به صفحات عمومی")')).toBeVisible();
    await expect(page.locator('a:has-text("ورود به بازارگاه")')).toBeVisible();
    
    // Locale switcher present
    await expect(page.locator('nav[aria-label="زبان"]')).toBeVisible();
  });

  test('English locale loads correctly', async ({ page }) => {
    await page.goto('/en');
    await expect(page).toHaveTitle(/HyDroMa/);
    await expect(page.locator('text=Smart landscape management')).toBeVisible();
    await expect(page.locator('a:has-text("Enter public pages")')).toBeVisible();
    await expect(page.locator('a:has-text("Enter the marketplace")')).toBeVisible();
  });

  test('Arabic locale loads with RTL', async ({ page }) => {
    await page.goto('/ar');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('text=إدارة ذكية')).toBeVisible();
  });

  test('Chinese locale loads', async ({ page }) => {
    await page.goto('/zh');
    await expect(page.locator('text=智能景观管理')).toBeVisible();
  });
});

test.describe('Cover Page - Navigation', () => {
  test('CTA "ورود به صفحات عمومی" navigates to /home', async ({ page }) => {
    await page.goto('/fa');
    await page.click('a:has-text("ورود به صفحات عمومی")');
    await expect(page).toHaveURL(/\/fa\/home/);
    await expect(page.locator('h1')).toContainText('هیدروما نوژین — پلتفرم احیای مَنظر');
  });

  test('CTA "ورود به بازارگاه" navigates to /market', async ({ page }) => {
    await page.goto('/fa');
    await page.click('a:has-text("ورود به بازارگاه")');
    await expect(page).toHaveURL(/\/fa\/market/);
    await expect(page.locator('h1')).toContainText('بازارگاه');
  });
});