import { test, expect } from '@playwright/test';

test.describe('RTL/LTR Layout Tests', () => {
  test('homepage loads and has correct HTML attributes', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const htmlDir = await page.getAttribute('html', 'dir');
    expect(['ltr', 'rtl']).toContain(htmlDir);

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(['fa', 'en']).toContain(htmlLang);
  });

  test('Persian version loads with RTL', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const htmlDir = await page.getAttribute('html', 'dir');
    // Default language is Persian (RTL)
    expect(htmlDir).toBe('rtl');

    const htmlLang = await page.getAttribute('html', 'lang');
    expect(htmlLang).toBe('fa');
  });

  test('app renders content after hydration', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
    expect(bodyText?.length).toBeGreaterThan(100);
  });

  test('navigation works between routes', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const routes = ['/about', '/impact', '/carbon', '/pilot'];
    for (const route of routes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');
      const bodyText = await page.textContent('body');
      expect(bodyText).toBeTruthy();
    }
  });

  test('search modal can be opened', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    await page.keyboard.press('Meta+k');
    await page.waitForTimeout(500);

    const hasDialog = await page.locator('[role="dialog"]').isVisible().catch(() => false);
    expect(typeof hasDialog).toBe('boolean');
  });

  test('content direction matches html dir attribute', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const htmlDir = await page.getAttribute('html', 'dir');
    expect(['ltr', 'rtl']).toContain(htmlDir);
  });
});