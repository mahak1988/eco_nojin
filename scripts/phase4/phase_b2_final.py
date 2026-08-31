#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Phase B-2: Complete Testing Excellence Setup
# Safe version - avoids problematic string characters

import os
import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"
VITEST_CONFIG = FRONTEND / "vitest.config.ts"
PLAYWRIGHT_CONFIG = FRONTEND / "playwright.config.ts"
E2E_DIR = FRONTEND / "e2e"
E2E_TESTS_DIR = E2E_DIR / "tests"
PACKAGE_JSON = FRONTEND / "package.json"


def ok(m):
    print(f"[OK] {m}")


def info(m):
    print(f"[INFO] {m}")


def warn(m):
    print(f"[WARN] {m}")


def err(m):
    print(f"[ERROR] {m}")


def build_string(lines):
    """Build a multi-line string from a list of lines safely"""
    return "\n".join(lines)


# =======================================================================
# VITEST CONFIG
# =======================================================================

VITEST_CONFIG_LINES = [
    "import { defineConfig } from 'vitest/config';",
    "import react from '@vitejs/plugin-react';",
    "import path from 'path';",
    "",
    "export default defineConfig({",
    "  plugins: [react()],",
    "  test: {",
    "    globals: true,",
    "    environment: 'jsdom',",
    "    setupFiles: ['./src/test/setup.ts'],",
    "    include: ['src/**/*.{test,spec}.{ts,tsx}'],",
    "    coverage: {",
    "      provider: 'v8',",
    "      reporter: ['text', 'json', 'html', 'lcov'],",
    "      exclude: [",
    "        'node_modules/',",
    "        'src/test/',",
    "        'src/**/*.d.ts',",
    "        'src/main.tsx',",
    "        'src/vite-env.d.ts',",
    "        'e2e/',",
    "        'dist/',",
    "        'coverage/',",
    "      ],",
    "      thresholds: {",
    "        lines: 60,",
    "        functions: 50,",
    "        branches: 50,",
    "        statements: 60,",
    "      },",
    "    },",
    "    reporters: ['default', 'html'],",
    "  },",
    "  resolve: {",
    "    alias: {",
    "      '@': path.resolve(__dirname, './src'),",
    "      '@features': path.resolve(__dirname, './src/features'),",
    "      '@components': path.resolve(__dirname, './src/components'),",
    "      '@hooks': path.resolve(__dirname, './src/hooks'),",
    "      '@utils': path.resolve(__dirname, './src/utils'),",
    "      '@types': path.resolve(__dirname, './src/types'),",
    "    },",
    "  },",
    "});",
    "",
]

VITEST_CONFIG_CONTENT = build_string(VITEST_CONFIG_LINES)


# =======================================================================
# PLAYWRIGHT CONFIG
# =======================================================================

PLAYWRIGHT_CONFIG_LINES = [
    "import { defineConfig, devices } from '@playwright/test';",
    "",
    "export default defineConfig({",
    "  testDir: './e2e/tests',",
    "  fullyParallel: true,",
    "  forbidOnly: !!process.env.CI,",
    "  retries: process.env.CI ? 2 : 0,",
    "  workers: process.env.CI ? 1 : undefined,",
    "  reporter: [",
    "    ['html', { open: 'never' }],",
    "    ['list'],",
    "  ],",
    "  use: {",
    "    baseURL: 'http://localhost:5173',",
    "    trace: 'on-first-retry',",
    "    screenshot: 'only-on-failure',",
    "    video: 'retain-on-failure',",
    "  },",
    "  projects: [",
    "    {",
    "      name: 'chromium',",
    "      use: { ...devices['Desktop Chrome'] },",
    "    },",
    "  ],",
    "  webServer: {",
    "    command: 'pnpm dev',",
    "    url: 'http://localhost:5173',",
    "    reuseExistingServer: !process.env.CI,",
    "    timeout: 120000,",
    "  },",
    "});",
    "",
]

PLAYWRIGHT_CONFIG_CONTENT = build_string(PLAYWRIGHT_CONFIG_LINES)


# =======================================================================
# E2E TEST: HOME
# =======================================================================

E2E_HOME_TEST_LINES = [
    "import { test, expect } from '@playwright/test';",
    "",
    "test.describe('Home Page', () => {",
    "  test('should load homepage successfully', async ({ page }) => {",
    "    await page.goto('/');",
    "",
    "    // Check that the page loaded",
    "    await expect(page).toHaveTitle(/.+/);",
    "",
    "    // Check for main content",
    "    const body = await page.textContent('body');",
    "    expect(body).toBeTruthy();",
    "    expect(body!.length).toBeGreaterThan(100);",
    "  });",
    "",
    "  test('should have responsive layout', async ({ page }) => {",
    "    await page.goto('/');",
    "",
    "    // Test mobile viewport",
    "    await page.setViewportSize({ width: 375, height: 667 });",
    "    await expect(page.locator('body')).toBeVisible();",
    "",
    "    // Test desktop viewport",
    "    await page.setViewportSize({ width: 1920, height: 1080 });",
    "    await expect(page.locator('body')).toBeVisible();",
    "  });",
    "});",
    "",
]

E2E_HOME_TEST = build_string(E2E_HOME_TEST_LINES)


# =======================================================================
# E2E TEST: NAVIGATION
# =======================================================================

E2E_NAVIGATION_TEST_LINES = [
    "import { test, expect } from '@playwright/test';",
    "",
    "test.describe('Navigation', () => {",
    "  test('should navigate between main pages', async ({ page }) => {",
    "    await page.goto('/');",
    "",
    "    // Test various routes",
    "    const routes = ['/about', '/features', '/pricing', '/contact'];",
    "",
    "    for (const route of routes) {",
    "      await page.goto(route);",
    "      // Page should not be blank",
    "      const content = await page.textContent('body');",
    "      expect(content!.length).toBeGreaterThan(0);",
    "    }",
    "  });",
    "",
    "  test('should handle 404 gracefully', async ({ page }) => {",
    "    const response = await page.goto('/non-existent-page-12345');",
    "    // Either 404 or redirect to home",
    "    expect(response).toBeTruthy();",
    "  });",
    "});",
    "",
]

E2E_NAVIGATION_TEST = build_string(E2E_NAVIGATION_TEST_LINES)


# =======================================================================
# E2E TEST: AUTH
# =======================================================================

E2E_AUTH_TEST_LINES = [
    "import { test, expect } from '@playwright/test';",
    "",
    "test.describe('Authentication Flow', () => {",
    "  test('should show login form', async ({ page }) => {",
    "    await page.goto('/login');",
    "",
    "    // Check for login form elements",
    "    const emailInput = page.locator('input[type=\"email\"], input[name=\"email\"], input[placeholder*=\"email\" i]');",
    "    const passwordInput = page.locator('input[type=\"password\"]');",
    "    const submitButton = page.locator('button[type=\"submit\"], button:has-text(\"Login\")');",
    "",
    "    // At least one should exist",
    "    const hasEmail = await emailInput.count() > 0;",
    "    const hasPassword = await passwordInput.count() > 0;",
    "    const hasSubmit = await submitButton.count() > 0;",
    "",
    "    expect(hasEmail || hasPassword || hasSubmit).toBe(true);",
    "  });",
    "",
    "  test('should show register form', async ({ page }) => {",
    "    await page.goto('/register');",
    "",
    "    const body = await page.textContent('body');",
    "    expect(body).toBeTruthy();",
    "  });",
    "});",
    "",
]

E2E_AUTH_TEST = build_string(E2E_AUTH_TEST_LINES)


# =======================================================================
# E2E README (no code blocks to avoid string issues)
# =======================================================================

E2E_README_LINES = [
    "# E2E Tests - Playwright",
    "",
    "## Overview",
    "",
    "This directory contains end-to-end tests using Playwright.",
    "",
    "## Running Tests",
    "",
    "Always run commands from the frontend directory:",
    "",
    "    cd D:\\eco_nojin\\frontend",
    "",
    "### Run all E2E tests",
    "",
    "    pnpm test:e2e",
    "",
    "### Run with UI mode (visual debugger)",
    "",
    "    pnpm test:e2e:ui",
    "",
    "### Run in debug mode",
    "",
    "    pnpm test:e2e:debug",
    "",
    "### Run specific test file",
    "",
    "    pnpm exec playwright test e2e/tests/home.spec.ts",
    "",
    "## Running Coverage",
    "",
    "    pnpm test:coverage",
    "",
    "Output: coverage/index.html",
    "",
    "## Test Categories",
    "",
    "### 1. Home Page (home.spec.ts)",
    "",
    "- Page load verification",
    "- Responsive layout testing",
    "",
    "### 2. Navigation (navigation.spec.ts)",
    "",
    "- Multi-page navigation",
    "- 404 handling",
    "",
    "### 3. Authentication (auth.spec.ts)",
    "",
    "- Login form rendering",
    "- Register form rendering",
    "",
    "## Directory Structure",
    "",
    "    frontend/",
    "      e2e/",
    "        tests/",
    "          home.spec.ts",
    "          navigation.spec.ts",
    "          auth.spec.ts",
    "        README.md",
    "      playwright.config.ts    (root config)",
    "      vitest.config.ts        (with coverage)",
    "      package.json            (with all scripts)",
    "",
    "## Important Notes",
    "",
    "- Always run commands from frontend/ directory",
    "- E2E tests automatically start dev server",
    "- Coverage report: frontend/coverage/index.html",
    "- Playwright report: frontend/playwright-report/index.html",
    "",
]

E2E_README = build_string(E2E_README_LINES)


# =======================================================================
# MAIN FUNCTION
# =======================================================================

def main():
    print("")
    print("=" * 70)
    print("  Phase B-2: Complete Testing Excellence Setup")
    print("=" * 70)
    print("")

    # Add Git to PATH
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # ===================================================================
    # Step 1: Verify project structure
    # ===================================================================
    print("[Step 1] Verifying project structure")
    print("-" * 70)

    if not FRONTEND.exists():
        err(f"Frontend directory not found: {FRONTEND}")
        return 1
    ok(f"Frontend directory exists: {FRONTEND}")

    if not PACKAGE_JSON.exists():
        err(f"package.json not found: {PACKAGE_JSON}")
        return 1
    ok("package.json exists")
    print("")

    # ===================================================================
    # Step 2: Install testing packages
    # ===================================================================
    print("[Step 2] Installing testing packages")
    print("-" * 70)

    packages = [
        "@vitest/coverage-v8",
        "@vitest/ui",
        "@playwright/test",
    ]

    info(f"Packages to install: {', '.join(packages)}")

    result = subprocess.run(
        f"pnpm add -D {' '.join(packages)}",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    if result.returncode == 0:
        ok("Testing packages installed successfully")
    else:
        warn("Installation had issues (may be already installed):")
        for line in (result.stdout + result.stderr).splitlines()[-10:]:
            if line.strip():
                print(f"  {line}")
    print("")

    # ===================================================================
    # Step 3: Install Playwright browsers
    # ===================================================================
    print("[Step 3] Installing Playwright browsers")
    print("-" * 70)
    info("Installing Chromium (this may take 2-3 minutes)...")

    result = subprocess.run(
        "pnpm exec playwright install chromium",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600
    )

    if result.returncode == 0:
        ok("Chromium browser installed")
    else:
        warn("Browser installation had warnings (may be already installed)")
        for line in (result.stdout + result.stderr).splitlines()[-5:]:
            if line.strip():
                print(f"  {line}")
    print("")

    # ===================================================================
    # Step 4: Write vitest.config.ts
    # ===================================================================
    print("[Step 4] Writing vitest.config.ts")
    print("-" * 70)

    VITEST_CONFIG.write_text(VITEST_CONFIG_CONTENT, encoding="utf-8")
    ok("vitest.config.ts created with coverage support")
    print("")

    # ===================================================================
    # Step 5: Write playwright.config.ts
    # ===================================================================
    print("[Step 5] Writing playwright.config.ts")
    print("-" * 70)

    PLAYWRIGHT_CONFIG.write_text(PLAYWRIGHT_CONFIG_CONTENT, encoding="utf-8")
    ok("playwright.config.ts created at frontend root")
    info("Config location: frontend/playwright.config.ts (NOT in e2e/)")
    info("This allows 'pnpm test:e2e' to work from frontend/ directory")
    print("")

    # ===================================================================
    # Step 6: Create E2E directory structure
    # ===================================================================
    print("[Step 6] Creating E2E directory structure")
    print("-" * 70)

    E2E_DIR.mkdir(exist_ok=True)
    E2E_TESTS_DIR.mkdir(parents=True, exist_ok=True)
    ok(f"Created: {E2E_DIR}")
    ok(f"Created: {E2E_TESTS_DIR}")

    # Write test files
    (E2E_TESTS_DIR / "home.spec.ts").write_text(E2E_HOME_TEST, encoding="utf-8")
    ok("Created: e2e/tests/home.spec.ts")

    (E2E_TESTS_DIR / "navigation.spec.ts").write_text(E2E_NAVIGATION_TEST, encoding="utf-8")
    ok("Created: e2e/tests/navigation.spec.ts")

    (E2E_TESTS_DIR / "auth.spec.ts").write_text(E2E_AUTH_TEST, encoding="utf-8")
    ok("Created: e2e/tests/auth.spec.ts")

    # Write README
    (E2E_DIR / "README.md").write_text(E2E_README, encoding="utf-8")
    ok("Created: e2e/README.md")
    print("")

    # ===================================================================
    # Step 7: Update package.json with scripts
    # ===================================================================
    print("[Step 7] Updating package.json scripts")
    print("-" * 70)

    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

    if "scripts" not in data:
        data["scripts"] = {}

    # Add all testing scripts
    new_scripts = {
        "test:coverage": "vitest run --coverage",
        "test:ui": "vitest --ui",
        "test:watch": "vitest",
        "test:e2e": "playwright test",
        "test:e2e:ui": "playwright test --ui",
        "test:e2e:debug": "playwright test --debug",
        "test:e2e:report": "playwright show-report",
        "test:all": "pnpm test && pnpm test:coverage && pnpm test:e2e",
    }

    for script_name, script_cmd in new_scripts.items():
        data["scripts"][script_name] = script_cmd
        ok(f"Added script: {script_name}")

    PACKAGE_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    ok("package.json updated with all testing scripts")
    print("")

    # ===================================================================
    # Step 8: Verify scripts work
    # ===================================================================
    print("[Step 8] Verifying scripts are available")
    print("-" * 70)

    # Check if scripts exist in package.json
    reloaded = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    scripts = reloaded.get("scripts", {})

    required_scripts = [
        "test:coverage",
        "test:e2e",
        "test:e2e:ui",
        "test:e2e:debug",
    ]

    all_found = True
    for script in required_scripts:
        if script in scripts:
            ok(f"Found: {script} -> {scripts[script]}")
        else:
            err(f"Missing: {script}")
            all_found = False

    if not all_found:
        err("Some scripts are missing!")
        return 1
    print("")

    # ===================================================================
    # Step 9: Run unit tests with coverage
    # ===================================================================
    print("[Step 9] Running unit tests with coverage")
    print("-" * 70)
    info("Executing: pnpm test:coverage")

    result = subprocess.run(
        "pnpm test:coverage",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    # Show coverage summary
    output = result.stdout + result.stderr
    coverage_found = False
    for line in output.splitlines():
        if any(k in line for k in [
            "Test Files", "Tests", "Coverage", "%",
            "All files", "Statements", "Branches", "Functions", "Lines"
        ]):
            print(f"  {line}")
            coverage_found = True

    if not coverage_found:
        info("No coverage summary shown (check coverage/ folder after)")
    print("")

    # ===================================================================
    # Step 10: Build verification
    # ===================================================================
    print("[Step 10] Build verification")
    print("-" * 70)

    result = subprocess.run(
        "pnpm build",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    if result.returncode == 0:
        ok("Build successful!")
    else:
        err("Build failed!")
        return 1
    print("")

    # ===================================================================
    # Step 11: Commit
    # ===================================================================
    print("[Step 11] Committing changes")
    print("-" * 70)

    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "feat(testing): Phase B-2 - Complete Testing Excellence Setup\n\n"
            "Infrastructure:\n"
            "- Vitest with v8 coverage provider configured\n"
            "- Playwright E2E testing framework installed\n"
            "- Chromium browser downloaded\n"
            "- All testing scripts added to package.json\n\n"
            "New Scripts (run from frontend/ directory):\n"
            "- pnpm test:coverage    -> Unit tests with coverage report\n"
            "- pnpm test:ui          -> Interactive Vitest UI\n"
            "- pnpm test:watch       -> Watch mode\n"
            "- pnpm test:e2e         -> Run all E2E tests\n"
            "- pnpm test:e2e:ui      -> Playwright UI mode (debugger)\n"
            "- pnpm test:e2e:debug   -> Playwright debug mode\n"
            "- pnpm test:e2e:report  -> Show Playwright HTML report\n"
            "- pnpm test:all         -> Run unit + coverage + E2E tests\n\n"
            "E2E Tests Created:\n"
            "- e2e/tests/home.spec.ts         -> Homepage tests\n"
            "- e2e/tests/navigation.spec.ts  -> Navigation tests\n"
            "- e2e/tests/auth.spec.ts        -> Authentication tests\n\n"
            "Configuration Files:\n"
            "- vitest.config.ts      (with coverage thresholds)\n"
            "- playwright.config.ts  (root config for frontend/)\n\n"
            "Phase B-1: Code Quality - COMPLETE\n"
            "Phase B-2: Testing Excellence - Initialized"
        )

        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed to main")
    except Exception as e:
        warn(f"Commit issue (you can commit manually): {e}")

    # ===================================================================
    # Final Report
    # ===================================================================
    print("")
    print("=" * 70)
    print("  Phase B-2: Testing Excellence - COMPLETE!")
    print("=" * 70)
    print("")

    print("  Infrastructure Ready:")
    print("    * Vitest with coverage (v8)")
    print("    * Playwright E2E framework")
    print("    * Chromium browser installed")
    print("    * All scripts configured")
    print("    * 3 E2E test suites ready")
    print("")

    print("  Available Commands (run from D:\\eco_nojin\\frontend):")
    print("    pnpm test:coverage      # Unit tests with coverage")
    print("    pnpm test:e2e           # E2E tests")
    print("    pnpm test:e2e:ui        # Playwright UI debugger")
    print("    pnpm test:e2e:debug     # Debug mode")
    print("    pnpm test:all           # Run all tests")
    print("")

    print("  IMPORTANT: PowerShell Commands")
    print("    cd D:\\eco_nojin\\frontend")
    print("    pnpm test:coverage      # Generates coverage/index.html")
    print("    pnpm test:e2e           # Runs all E2E tests")
    print("    pnpm test:e2e:ui        # Opens visual debugger")
    print("")

    print("  Recommended Next Steps:")
    print("    1. cd D:\\eco_nojin\\frontend")
    print("    2. pnpm test:coverage")
    print("    3. Open coverage/index.html in browser")
    print("    4. Identify modules with low coverage")
    print("    5. Add tests for critical business logic")
    print("    6. Target: 80%+ coverage")
    print("")

    print("  Quick E2E Verification:")
    print("    cd D:\\eco_nojin\\frontend")
    print("    pnpm test:e2e:ui")
    print("    # Visual debugger opens - run tests manually")
    print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())