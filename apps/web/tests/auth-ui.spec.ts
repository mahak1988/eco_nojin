import { expect, test } from '@playwright/test';

test('renders the localized login and signup entry points', async ({ page }) => {
  await page.goto('/fa/auth/login');
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.getByLabel('ایمیل')).toBeVisible();
  await expect(page.locator('input[name="password"]')).toBeVisible();
  await expect(page.getByRole('link', { name: 'ساخت حساب کاربری' })).toBeVisible();

  await page.getByRole('link', { name: 'ساخت حساب کاربری' }).click();
  await expect(page).toHaveURL(/\/fa\/auth\/signup/);
  await expect(page.getByLabel('نام و نام خانوادگی')).toBeVisible();
  await expect(page.locator('input[name="confirmPassword"]')).toBeVisible();
});
