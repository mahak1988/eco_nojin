#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Remove ffmpeg requirement from Playwright config
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
PLAYWRIGHT_CONFIG = FRONTEND / "playwright.config.ts"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")


CONFIG_FIXED = """import { defineConfig, devices } from '@playwright/test';

// Detect if we should use system Chrome
const useSystemChrome = process.env.PLAYWRIGHT_USE_SYSTEM_CHROME !== 'false';

export default defineConfig({
  testDir: './e2e/tests',
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
    // Disable video/trace/screenshot to avoid ffmpeg download requirement
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    launchOptions: {
      channel: 'chrome',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
  },
  projects: [
    {
      name: 'chromium',
      use: {
        channel: 'chrome',
        ...devices['Desktop Chrome'],
      },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 180000,
  },
});
"""


def main():
    print("")
    print("=" * 70)
    print("  Fix: Remove ffmpeg requirement")
    print("=" * 70)
    print("")

    # Step 1: Update config
    print("[Step 1] Updating playwright.config.ts")
    print("-" * 70)
    
    PLAYWRIGHT_CONFIG.write_text(CONFIG_FIXED, encoding="utf-8")
    ok("Config updated - disabled video/trace/screenshot")
    info("ffmpeg no longer required")
    print("")

    # Step 2: Commit
    print("[Step 2] Committing changes")
    print("-" * 70)
    
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "fix(e2e): disable video recording to avoid ffmpeg requirement\n\n"
            "Changed in playwright.config.ts:\n"
            "- video: 'retain-on-failure' -> video: 'off'\n"
            "- trace: 'on-first-retry' -> trace: 'off'\n"
            "- screenshot: 'only-on-failure' -> screenshot: 'off'\n\n"
            "Reason: PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 prevents\n"
            "ffmpeg download, which is required for video recording.\n"
            "Disabling these features avoids the CDN 403 error."
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        info(f"Commit issue: {e}")

    # Final Report
    print("")
    print("=" * 70)
    print("  Fix Complete!")
    print("=" * 70)
    print("")
    print("  Now run E2E tests:")
    print("    cd D:\\eco_nojin\\frontend")
    print("    .\\run-e2e.ps1 ui")
    print("")
    print("  Note: UI mode will:")
    print("    1. Start dev server (pnpm dev) - wait 30-60 seconds")
    print("    2. Open Playwright UI in browser")
    print("    3. You can then run tests interactively")
    print("")

    return 0


if __name__ == "__main__":
    sys.exit(main())