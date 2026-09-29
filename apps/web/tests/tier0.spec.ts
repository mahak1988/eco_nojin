import { expect, test } from '@playwright/test';

const routes = [
  '/fa/admin',
  '/fa/research',
  '/fa/research/workspace/experiment-1',
  '/fa/system',
  '/fa/system/pwa-update',
  '/fa/system/locale-fallback',
  '/fa/help',
  '/fa/workspace',
  '/fa/workspace/overview',
  '/en/research',
];

for (const route of routes) {
  test(`${route} renders without a missing message`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
    await expect(page.locator('h1').first()).toBeVisible();
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}

/**
 * `ProvenanceStamp` renders `label ?? children`, so a call site passing both a
 * label and a heading silently dropped the heading. Every public surface has to
 * expose its heading; the colocated unit test guards the source, this guards
 * the rendered result.
 */
const headingRoutes = [
  '/fa/public/home',
  '/en/public/home',
  '/fa/public/why',
  '/fa/public/visit',
  '/fa/public/model-count',
  '/fa/public/services/overview',
  '/fa/public/policy/terms',
  '/fa/public/goals/mission',
  '/fa/public/education/glossary',
];

for (const route of headingRoutes) {
  test(`${route} exposes its page heading`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response?.status()).toBeLessThan(500);
    // A page that drops its heading behind a `ProvenanceStamp` label is the
    // defect this guards, and a second level-one heading is as wrong as none:
    // `FivePart` supplies a heading, so the pages that also render their own
    // title pass `headingLevel={2}` to keep exactly one.
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.locator('body')).not.toContainText('MISSING_MESSAGE');
  });
}

test('answers an unknown path with 404, not a 200 with a not-found body', async ({ page }) => {
  // `app/[locale]/loading.tsx` used to stream a 200 shell for the whole locale,
  // which meant `notFound()` rendered the right body on a wrong status. A
  // locale-wide loading boundary cannot be reinstated for this reason; the
  // boundaries that remain are scoped to the segments that await the gateway.
  const response = await page.goto('/fa/this-route-does-not-exist-xyz');
  expect(response?.status()).toBe(404);
  await expect(page.locator('h1')).toHaveCount(1);
});
