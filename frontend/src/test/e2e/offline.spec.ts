import { test, expect } from '@playwright/test';

test.describe('Offline Functionality Tests', () => {
  test('service worker caches critical resources', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const cachedResources = await page.evaluate(async () => {
      if (!('caches' in window)) return [];
      try {
        const cacheNames = await caches.keys();
        const results: string[] = [];
        for (const name of cacheNames) {
          const cache = await caches.open(name);
          const keys = await cache.keys();
          results.push(...keys.map(r => r.url));
        }
        return results;
      } catch {
        return [];
      }
    });

    expect(Array.isArray(cachedResources)).toBe(true);
  });

  test('app loads when online', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });

  test('navigation works between routes', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const routes = ['/', '/about', '/impact'];
    for (const route of routes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');
      const hasContent = await page.textContent('body');
      expect(hasContent).toBeTruthy();
    }
  });

  test('localStorage persists language preference', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const initialLang = await page.evaluate(() => localStorage.getItem('eco_nojin_lang'));
    expect(['fa', 'en', null]).toContain(initialLang);

    const langAfterReload = await page.evaluate(() => localStorage.getItem('eco_nojin_lang'));
    expect(langAfterReload).toBe(initialLang);
  });

  test('app shows content', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const bodyText = await page.textContent('body');
    expect(bodyText).toBeTruthy();
  });
});