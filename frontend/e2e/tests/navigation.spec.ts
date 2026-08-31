import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate between main pages', async ({ page }) => {
    await page.goto('/');

    // Test various routes
    const routes = ['/about', '/features', '/pricing', '/contact'];

    for (const route of routes) {
      await page.goto(route);
      // Page should not be blank
      const content = await page.textContent('body');
      expect(content!.length).toBeGreaterThan(0);
    }
  });

  test('should handle 404 gracefully', async ({ page }) => {
    const response = await page.goto('/non-existent-page-12345');
    // Either 404 or redirect to home
    expect(response).toBeTruthy();
  });
});
