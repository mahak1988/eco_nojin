import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

/**
 * The manual reference surfaces bind eight published `GET /api/v1/manual/*`
 * contracts. These tests do not assert dataset values, because the reference
 * SQLite file is a deployment input and a test must not depend on its contents.
 * They assert what the page owes the reader regardless of whether the gateway
 * answered: a heading, no placeholder copy, an honest source stamp, and no
 * accessibility regression.
 */

const collectionRoutes = [
  '/fa/learn/manual/sites',
  '/fa/learn/manual/status',
  '/fa/learn/manual/crop-params',
  '/fa/learn/manual/soil-regions',
  '/fa/learn/manual/crop-calendar',
  '/en/learn/manual/sites',
];

for (const route of collectionRoutes) {
  test(`${route} renders without a missing message`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}

test.describe('manual reference routes', () => {
  test('names the gateway path it read', async ({ page }) => {
    await page.goto('/fa/learn/manual/sites');
    await expect(page.locator('body')).toContainText('/api/v1/manual/sites');
  });

  test('carries provenance that names the real source', async ({ page }) => {
    await page.goto('/fa/learn/manual/status');
    const stamp = page.locator('[data-provenance="/api/v1/manual/status"]').first();
    await expect(stamp).toBeVisible();
  });

  test('never presents a record for a site id the dataset cannot hold', async ({ page }) => {
    // The gateway addresses sites by integer key, so a non-numeric id is
    // refused before any request is made. The app answers an unknown path with
    // HTTP 200 and a not-found body, so the assertion is on the content: the
    // site record and its source path must never appear.
    await page.goto('/fa/learn/manual/sites/not-a-number');
    await expect(page.locator('body')).not.toContainText('/api/v1/manual/sites/not-a-number');
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });

  test('keeps the site search usable without JavaScript', async ({ page }) => {
    await page.goto('/fa/learn/manual/sites');
    // Scoped to the form: the assertion is about the form, and an unscoped id
    // locator is fragile while the page streams.
    const form = page.locator('form').first();
    const input = form.locator('#manual-site-search');
    await expect(input).toBeVisible();
    await input.fill('rasht');
    await Promise.all([page.waitForURL(/q=rasht/), form.locator('button[type="submit"]').click()]);
    await expect(page.locator('body')).toContainText('/api/v1/manual/sites?q=rasht');
  });

  test('has no serious accessibility violations on a collection route', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto('/fa/learn/manual/soil-regions');
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const serious = results.violations.filter(
      (violation) => violation.impact === 'critical' || violation.impact === 'serious',
    );
    expect(serious, JSON.stringify(serious, null, 2)).toHaveLength(0);
  });
});
