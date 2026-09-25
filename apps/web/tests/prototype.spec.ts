import { expect, test } from '@playwright/test';

test.describe('Sustainability prototype', () => {
  test('renders in Persian RTL and remains usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/fa/prototype');

    await expect(
      page.getByRole('heading', { name: 'از داده‌های زنده تا تصمیم پایدار' }),
    ).toBeVisible();
    await expect(page.locator('main')).toHaveAttribute('dir', 'rtl');
    await expect(page.getByRole('button', { name: 'خاک' })).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test('integrates the impact preview on the platform page', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/fa/platform');

    await expect(page.getByRole('heading', { name: 'اجزای پلتفرم' })).toBeVisible();
    await expect(
      page.getByRole('heading', { name: 'اثر را از داده و شواهد جدا کن' }),
    ).toBeVisible();
    await expect(page.getByText(/دادهٔ پلتفرم|اتصال زنده در دسترس نیست/).first()).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test('switches map layers and scenario values', async ({ page }) => {
    await page.goto('/en/prototype');

    await page.getByRole('button', { name: 'Biodiversity', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Cover and ecological form' })).toBeVisible();

    await page.getByRole('button', { name: 'Accelerated' }).click();
    await expect(page.getByText('−15%')).toBeVisible();
  });
});
