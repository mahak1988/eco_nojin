import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
 * The contract-light surfaces bind published routes that declare no field, so
 * these tests assert the guarantees that hold whether or not the gateway is up:
 * a heading, the exact source path on the page, no placeholder copy, and no
 * accessibility regression. They never assert a value, because the value is a
 * deployment input.
 */

const dashboardSlugs = [
  'full',
  'projects',
  'carbon',
  'analytics',
  'weather',
  'satellite',
  'soil',
  'mrv',
  'simulations',
  'tourism',
  'test',
];

for (const slug of dashboardSlugs) {
  test(`/system/dashboard/public/${slug} renders its heading and source`, async ({ page }) => {
    const response = await page.goto(`/fa/system/dashboard/public/${slug}`);
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('h1').first()).toBeVisible();
    // The page must name the gateway path it read, so a reader can repeat the
    // request themselves.
    await expect(page.locator('body')).toContainText(`/dashboard/public/${slug}`);
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}

const namedSurfaces = [
  { route: '/fa/market/stats', source: '/api/v1/marketplace/stats' },
  { route: '/fa/market/producers', source: '/api/v1/marketplace/producers' },
  { route: '/fa/learn/content/search', source: '/api/v1/content/search' },
];

for (const { route, source } of namedSurfaces) {
  test(`${route} renders its heading and source`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('body')).toContainText(source);
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}

test.describe('contract-light surfaces', () => {
  test('keeps the content search usable without JavaScript', async ({ page }) => {
    await page.goto('/fa/learn/content/search');
    // Scoped to the form: an unscoped id locator is fragile while the public
    // surface streams, and this test is about the form, not the outline.
    const form = page.locator('form').first();
    const input = form.locator('#content-search');
    await expect(input).toBeVisible();
    await input.fill('soil');
    await Promise.all([page.waitForURL(/q=soil/), form.locator('button[type="submit"]').click()]);
    await expect(page.locator('body')).toContainText('q=soil');
  });

  test('never sends an empty content search term to the gateway', async ({ page }) => {
    // `q` is a required parameter, so the empty form must not produce a request.
    const requests: string[] = [];
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/content/search')) requests.push(request.url());
    });
    await page.goto('/fa/learn/content/search');
    await expect(page.locator('h1').first()).toBeVisible();
    expect(requests).toEqual([]);
  });

  test('has no serious accessibility violations on a dashboard surface', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/fa/system/dashboard/public/carbon');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const serious = results.violations.filter(
      (violation) => violation.impact === 'critical' || violation.impact === 'serious',
    );
    expect(serious, JSON.stringify(serious, null, 2)).toHaveLength(0);
  });
});
