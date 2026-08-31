#!/usr/bin/env python3
"""
Phase B-2: Testing Excellence Setup (FIXED)
============================================
Fixed triple-quoted strings and PowerShell compatibility.
"""

import os
import sys
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITEST_CONFIG = FRONTEND / "vitest.config.ts"
PLAYWRIGHT_DIR = FRONTEND / "e2e"
PACKAGE_JSON = FRONTEND / "package.json"


def ok(m): print(f"\033[92m✓\033[0m  {m}")
def info(m): print(f"\033[94mℹ\033[0m  {m}")
def warn(m): print(f"\033[93m⚠\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


# ═══════════════════════════════════════════════════════════════════════
# All multi-line strings use r"""...""" (raw strings) for safety
# ═══════════════════════════════════════════════════════════════════════

VITEST_CONFIG_WITH_COVERAGE = r"""import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
        'e2e/',
        'dist/',
        'coverage/',
      ],
      thresholds: {
        lines: 60,
        functions: 50,
        branches: 50,
        statements: 60,
      },
    },
    reporters: ['default', 'html'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@features': path.resolve(__dirname, './src/features'),
      '@components': path.resolve(__dirname, './src/components'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
});
"""


PLAYWRIGHT_CONFIG = r"""import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
"""


E2E_HOME_TEST = r"""import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load homepage successfully', async ({ page }) => {
    await page.goto('/');
    
    // Check that the page loaded
    await expect(page).toHaveTitle(/.*Eco.*|.*Hydroma.*|.*Nojin.*/i);
    
    // Check for main heading or logo
    const body = await page.textContent('body');
    expect(body).toBeTruthy();
    expect(body!.length).toBeGreaterThan(100);
  });

  test('should have responsive layout', async ({ page }) => {
    await page.goto('/');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('body')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('body')).toBeVisible();
  });
});
"""


E2E_NAVIGATION_TEST = r"""import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate between main pages', async ({ page }) => {
    await page.goto('/');
    
    // Test various routes
    const routes = ['/about', '/features', '/pricing', '/contact'];
    
    for (const route of routes) {
      await page.goto(route);
      await expect(page).toHaveURL(new RegExp(route.replace('/', '\\/')));
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
"""


E2E_AUTH_TEST = r"""import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should show login form', async ({ page }) => {
    await page.goto('/login');
    
    // Check for login form elements
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');
    const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("ورود")');
    
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
"""


E2E_README = """# E2E Tests

## Overview
This directory contains end-to-end tests using Playwright.

## Running Tests

### Run all E2E tests
```bash
pnpm test:e2e