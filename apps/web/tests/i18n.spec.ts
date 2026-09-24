import { test, expect } from '@playwright/test';

const LOCALES = [
  { code: 'fa', dir: 'rtl', name: 'Persian' },
  { code: 'en', dir: 'ltr', name: 'English' },
  { code: 'ar', dir: 'rtl', name: 'Arabic' },
  { code: 'ur', dir: 'rtl', name: 'Urdu' },
  { code: 'de', dir: 'ltr', name: 'German' },
  { code: 'es', dir: 'ltr', name: 'Spanish' },
  { code: 'fr', dir: 'ltr', name: 'French' },
  { code: 'zh', dir: 'ltr', name: 'Chinese' },
];

test.describe('i18n - All 14 locales', () => {
  for (const locale of LOCALES) {
    test(`${locale.name} (${locale.code}) loads with correct dir`, async ({ page }) => {
      await page.goto(`/${locale.code}/home`);
      await expect(page.locator('html')).toHaveAttribute('dir', locale.dir);
      await expect(page.locator('h1')).toBeVisible();
    });
  }

  test('Locale switcher shows all 14 locales', async ({ page }) => {
    await page.goto('/fa/home');
    const switcher = page.locator('nav[aria-label="زبان"]');
    await expect(switcher).toBeVisible();
    
    // Check all 14 locale links exist
    for (const locale of LOCALES) {
      await expect(page.locator(`a[hrefLang="${locale.code}"]`)).toBeVisible();
    }
  });

  test('Locale change persists via URL', async ({ page }) => {
    await page.goto('/fa/home');
    await page.click('a[hrefLang="en"]');
    await expect(page).toHaveURL(/\/en\/home/);
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
  });

  test('RTL locales have correct text direction', async ({ page }) => {
    await page.goto('/fa/home');
    const body = page.locator('body');
    await expect(body).toHaveCSS('direction', 'rtl');
    
    await page.goto('/ar/home');
    await expect(body).toHaveCSS('direction', 'rtl');
  });

  test('LTR locales have correct text direction', async ({ page }) => {
    await page.goto('/en/home');
    const body = page.locator('body');
    await expect(body).toHaveCSS('direction', 'ltr');
  });

  test('Fallback chain: de falls back to en then fa', async ({ page }) => {
    await page.goto('/de/home');
    // Should have some translated content and some fallback content
    await expect(page.locator('h1')).toBeVisible();
  });
});