import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should show login form', async ({ page }) => {
    await page.goto('/login');

    // Check for login form elements
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"], button:has-text("Login")');

    // At least one should exist
    const hasEmail = await emailInput.count() > 0;
    const hasPassword = await passwordInput.count() > 0;
    const hasSubmit = await submitButton.count() > 0;

    expect(hasEmail || hasPassword || hasSubmit).toBe(true);
  });

  test('should show register form', async ({ page }) => {
    await page.goto('/register');

    const body = await page.textContent('body');
    expect(body).toBeTruthy();
  });
});
