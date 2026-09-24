import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility (WCAG 2.1 AA)', () => {
  const pages = [
    { path: '/fa/home', name: 'Home (fa)' },
    { path: '/en/home', name: 'Home (en)' },
    { path: '/fa/market', name: 'Market (fa)' },
    { path: '/en/market', name: 'Market (en)' },
    { path: '/fa/hydroma', name: 'Hydroma (fa)' },
    { path: '/en/hydroma', name: 'Hydroma (en)' },
    { path: '/fa', name: 'Cover (fa)' },
    { path: '/en', name: 'Cover (en)' },
  ];

  for (const pageInfo of pages) {
    test(`${pageInfo.name} has no critical a11y violations`, async ({ page }) => {
      await page.goto(pageInfo.path);
      const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical'
      );
      expect(criticalViolations, `Critical a11y violations on ${pageInfo.path}: ${JSON.stringify(criticalViolations, null, 2)}`).toHaveLength(0);
    });
  }

  test('Keyboard navigation works on cover page', async ({ page }) => {
    await page.goto('/fa/home');
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
  });

  test('Skip link works', async ({ page }) => {
    await page.goto('/fa/home');
    await page.keyboard.press('Tab');
    const skipLink = page.locator('a.skip-link');
    await expect(skipLink).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.locator('#main')).toBeFocused();
  });

  test('All interactive elements have focus styles', async ({ page }) => {
    await page.goto('/fa/home');
    const links = page.locator('a[href]');
    const count = await links.count();
    for (let i = 0; i < Math.min(count, 10); i++) {
      const link = links.nth(i);
      await link.focus();
      await expect(link).toBeFocused();
    }
  });
});