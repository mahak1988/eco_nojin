import { test, expect } from '@playwright/test';

test.describe('PWA Install Tests', () => {
  test('manifest.webmanifest is accessible and valid', async ({ page }) => {
    const response = await page.goto('/manifest.webmanifest');
    expect(response?.status()).toBe(200);

    const manifest = await response?.json();
    expect(manifest).toHaveProperty('name');
    expect(manifest).toHaveProperty('short_name');
    expect(manifest).toHaveProperty('start_url');
    expect(manifest).toHaveProperty('display', 'standalone');
    expect(manifest).toHaveProperty('theme_color');
    expect(manifest).toHaveProperty('background_color');
    expect(manifest.icons).toBeInstanceOf(Array);
    expect(manifest.icons.length).toBeGreaterThan(0);
  });

  test('service worker file is accessible', async ({ page }) => {
    const response = await page.goto('/sw.js');
    expect(response?.status()).toBe(200);
    const text = await response?.text();
    expect(text).toContain('precacheAndRoute');
  });

  test('icons are accessible', async ({ page }) => {
    const manifestResponse = await page.goto('/manifest.webmanifest');
    const manifest = await manifestResponse?.json();

    for (const icon of manifest.icons.slice(0, 3)) {
      const response = await page.goto(icon.src);
      expect(response?.status()).toBe(200);
    }
  });

  test('app loads correctly', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const title = await page.title();
    expect(title.length).toBeGreaterThan(0);
  });

  test('app has PWA meta tags', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('#root');

    const themeColor = await page.getAttribute('meta[name="theme-color"]', 'content');
    expect(themeColor).toBeTruthy();
  });
});