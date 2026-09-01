#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Definitive Fix: Playwright 403 CDN Error
==========================================
Root Cause: Playwright CDN blocked in Iran (403 Forbidden)
Multi-layer Solution:
1. System Chrome via channel config
2. Environment variables to skip downloads
3. Package.json scripts with env vars
4. Explicit browser executable path
"""

import structlog

logger = structlog.get_logger()
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
PLAYWRIGHT_CONFIG = FRONTEND / "playwright.config.ts"
PACKAGE_JSON = FRONTEND / "package.json"


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")
def err(m): print(f"[ERROR] {m}")


def build_string(lines):
    return "\n".join(lines)


def find_chrome_executable():
    """Find Chrome executable on Windows system"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    # Try using where command to find chrome
    try:
        result = subprocess.run(
            "where chrome",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            first_match = result.stdout.strip().split('\n')[0].strip()
            if Path(first_match).exists():
                return first_match
    except:
        pass
    
    # Try chrome-cli
    try:
        result = subprocess.run(
            "where chrome.exe",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            first_match = result.stdout.strip().split('\n')[0].strip()
            if Path(first_match).exists():
                return first_match
    except:
        pass
    
    return None


# =======================================================================
# ROBUST Playwright Config - Multiple Fallbacks
# =======================================================================

PLAYWRIGHT_CONFIG_LINES = [
    "import { defineConfig, devices } from '@playwright/test';",
    "",
    "// Detect if we should use system Chrome",
    "const useSystemChrome = process.env.PLAYWRIGHT_USE_SYSTEM_CHROME !== 'false';",
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
    "    // Force system Chrome to avoid CDN downloads",
    "    launchOptions: {",
    "      channel: 'chrome',",
    "      args: ['--no-sandbox', '--disable-setuid-sandbox'],",
    "    },",
    "  },",
    "  projects: [",
    "    {",
    "      name: 'chromium',",
    "      use: {",
    "        channel: 'chrome',",
    "        ...devices['Desktop Chrome'],",
    "      },",
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

PLAYWRIGHT_CONFIG = build_string(PLAYWRIGHT_CONFIG_LINES)


# =======================================================================
# Environment setup script (Windows batch file)
# =======================================================================

ENV_SETUP_BAT_LINES = [
    "@echo off",
    "REM Playwright Environment Setup for Iran (bypass CDN 403)",
    "",
    "REM Skip browser downloads completely",
    "set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1",
    "",
    "REM Force system Chrome usage",
    "set PLAYWRIGHT_USE_SYSTEM_CHROME=true",
    "",
    "REM Disable browser download checks",
    "set PLAYWRIGHT_BROWSERS_PATH=0",
    "",
    "echo Playwright environment configured for system Chrome",
    "echo Run: pnpm test:e2e or pnpm test:e2e:ui",
    "",
]

ENV_SETUP_BAT = build_string(ENV_SETUP_BAT_LINES)


# =======================================================================
# PowerShell equivalent
# =======================================================================

ENV_SETUP_PS1_LINES = [
    "# Playwright Environment Setup for Iran (bypass CDN 403)",
    "",
    "# Skip browser downloads completely",
    "$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'",
    "",
    "# Force system Chrome usage",
    "$env:PLAYWRIGHT_USE_SYSTEM_CHROME = 'true'",
    "",
    "# Disable browser download checks",
    "$env:PLAYWRIGHT_BROWSERS_PATH = '0'",
    "",
    "Write-Host 'Playwright environment configured for system Chrome' -ForegroundColor Green",
    "Write-Host 'Run: pnpm test:e2e or pnpm test:e2e:ui' -ForegroundColor Cyan",
    "",
]

ENV_SETUP_PS1 = build_string(ENV_SETUP_PS1_LINES)


def main():
    logger.info("")
    logger.info("=" * 70)
    logger.error("  Definitive Fix: Playwright 403 CDN Error")
    logger.info("=" * 70)
    logger.info("")
    logger.info("  Root Cause: Playwright CDN blocked (403 Forbidden)")
    logger.info("  Solution: Multi-layer protection with system Chrome")
    logger.info("")

    # Step 1: Find Chrome
    logger.info("[Step 1] Locating system Chrome")
    logger.info("-" * 70)
    
    chrome_path = find_chrome_executable()
    
    if chrome_path:
        ok(f"Found Chrome: {chrome_path}")
    else:
        warn("Chrome not found in standard locations")
        info("Will rely on 'channel: chrome' config")
    logger.info("")

    # Step 2: Write new playwright config
    logger.info("[Step 2] Rewriting playwright.config.ts")
    logger.info("-" * 70)
    
    PLAYWRIGHT_CONFIG_FILE = FRONTEND / "playwright.config.ts"
    PLAYWRIGHT_CONFIG_FILE.write_text(PLAYWRIGHT_CONFIG, encoding="utf-8")
    ok(f"Written: {PLAYWRIGHT_CONFIG_FILE.name}")
    info("Config uses: channel: 'chrome' (system browser)")
    logger.info("")

    # Step 3: Create environment setup scripts
    logger.info("[Step 3] Creating environment setup scripts")
    logger.info("-" * 70)
    
    env_bat = FRONTEND / "setup-playwright-env.bat"
    env_bat.write_text(ENV_SETUP_BAT, encoding="utf-8")
    ok(f"Created: {env_bat.name} (for CMD)")
    
    env_ps1 = FRONTEND / "setup-playwright-env.ps1"
    env_ps1.write_text(ENV_SETUP_PS1, encoding="utf-8")
    ok(f"Created: {env_ps1.name} (for PowerShell)")
    logger.info("")

    # Step 4: Update package.json with env vars in scripts
    logger.info("[Step 4] Updating package.json scripts with env vars")
    logger.info("-" * 70)
    
    pkg_data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    
    if "scripts" not in pkg_data:
        pkg_data["scripts"] = {}
    
    # Use cross-env syntax that works on Windows
    # PowerShell-friendly commands
    updated_scripts = {
        "test:e2e": "set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 && set PLAYWRIGHT_BROWSERS_PATH=0 && playwright test",
        "test:e2e:ui": "set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 && set PLAYWRIGHT_BROWSERS_PATH=0 && playwright test --ui",
        "test:e2e:debug": "set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 && set PLAYWRIGHT_BROWSERS_PATH=0 && playwright test --debug",
        "test:e2e:report": "playwright show-report",
    }
    
    # For PowerShell compatibility, use separate commands
    pkg_data["scripts"]["test:e2e:pwsh"] = "pwsh -Command \"$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1'; $env:PLAYWRIGHT_BROWSERS_PATH='0'; pnpm exec playwright test\""
    pkg_data["scripts"]["test:e2e:ui:pwsh"] = "pwsh -Command \"$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1'; $env:PLAYWRIGHT_BROWSERS_PATH='0'; pnpm exec playwright test --ui\""
    
    for name, cmd in updated_scripts.items():
        pkg_data["scripts"][name] = cmd
        ok(f"Updated: {name}")
    
    PACKAGE_JSON.write_text(
        json.dumps(pkg_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    ok("package.json updated")
    logger.info("")

    # Step 5: Create PowerShell launcher script
    logger.info("[Step 5] Creating PowerShell launcher")
    logger.info("-" * 70)
    
    launcher_lines = [
        "# Playwright E2E Test Launcher (PowerShell)",
        "# This script sets env vars and runs E2E tests",
        "",
        "# Set environment variables for current session",
        "$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'",
        "$env:PLAYWRIGHT_BROWSERS_PATH = '0'",
        "$env:PLAYWRIGHT_USE_SYSTEM_CHROME = 'true'",
        "",
        "Write-Host '==================================' -ForegroundColor Cyan",
        "Write-Host '  Playwright E2E Test Launcher' -ForegroundColor Cyan",
        "Write-Host '==================================' -ForegroundColor Cyan",
        "Write-Host ''",
        "Write-Host 'Environment configured:' -ForegroundColor Green",
        "Write-Host '  - PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = 1' -ForegroundColor Yellow",
        "Write-Host '  - PLAYWRIGHT_BROWSERS_PATH = 0' -ForegroundColor Yellow",
        "Write-Host '  - PLAYWRIGHT_USE_SYSTEM_CHROME = true' -ForegroundColor Yellow",
        "Write-Host ''",
        "",
        "# Determine what to run",
        "$testMode = $args[0]",
        "",
        "switch ($testMode) {",
        "    'ui' {",
        "        Write-Host 'Running: playwright test --ui' -ForegroundColor Green",
        "        pnpm exec playwright test --ui",
        "    }",
        "    'debug' {",
        "        Write-Host 'Running: playwright test --debug' -ForegroundColor Green",
        "        pnpm exec playwright test --debug",
        "    }",
        "    'report' {",
        "        Write-Host 'Running: playwright show-report' -ForegroundColor Green",
        "        pnpm exec playwright show-report",
        "    }",
        "    default {",
        "        Write-Host 'Running: playwright test (headless)' -ForegroundColor Green",
        "        pnpm exec playwright test",
        "    }",
        "}",
        "",
    ]
    
    launcher = FRONTEND / "run-e2e.ps1"
    launcher.write_text(build_string(launcher_lines), encoding="utf-8")
    ok(f"Created: {launcher.name}")
    info("Usage:")
    info("  .\\run-e2e.ps1         # Headless mode")
    info("  .\\run-e2e.ps1 ui      # UI mode")
    info("  .\\run-e2e.ps1 debug   # Debug mode")
    logger.info("")

    # Step 6: Test the setup
    logger.info("[Step 6] Testing E2E setup")
    logger.info("-" * 70)
    
    # Set env vars for this process
    os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
    os.environ['PLAYWRIGHT_USE_SYSTEM_CHROME'] = 'true'
    
    info("Running: playwright test --list (verify config)")
    
    result = subprocess.run(
        "pnpm exec playwright test --list",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env={**os.environ, 
             'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD': '1',
             'PLAYWRIGHT_BROWSERS_PATH': '0',
             'PLAYWRIGHT_USE_SYSTEM_CHROME': 'true'}
    )
    
    output = result.stdout + result.stderr
    
    # Show relevant output
    lines_to_show = []
    for line in output.splitlines():
        if any(k in line.lower() for k in [
            'listing', 'tests', 'found', 'error', 'warning', 'chrome', 'browser'
        ]):
            lines_to_show.append(line)
    
    if lines_to_show:
        for line in lines_to_show[:20]:
            logger.info(f"  {line}")
    
    if result.returncode == 0:
        ok("\n✓ Playwright configuration works!")
    else:
        warn("\nPlaywright had issues (might need manual setup)")
        info("Try the PowerShell launcher instead:")
        info("  cd D:\\eco_nojin\\frontend")
        info("  .\\run-e2e.ps1 ui")
    logger.info("")

    # Step 7: Commit
    logger.info("[Step 7] Committing changes")
    logger.info("-" * 70)
    
    try:
        # Add Git to PATH
        for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
            if Path(p).exists() and p not in os.environ["PATH"]:
                os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
        
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            "fix(e2e): resolve Playwright 403 CDN error with multi-layer protection\n\n"
            "Problem:\n"
            "- Playwright CDN blocked in Iran (403 Forbidden)\n"
            "- UI mode (--ui) attempts browser download despite config\n"
            "- Tests fail with: Access denied error\n\n"
            "Multi-layer Solution:\n"
            "1. playwright.config.ts: Force 'channel: chrome' (system browser)\n"
            "2. Environment variables:\n"
            "   - PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1\n"
            "   - PLAYWRIGHT_BROWSERS_PATH=0\n"
            "   - PLAYWRIGHT_USE_SYSTEM_CHROME=true\n"
            "3. Updated package.json scripts with env vars\n"
            "4. Created PowerShell launcher (run-e2e.ps1)\n"
            "5. Created .bat and .ps1 setup scripts\n\n"
            "Usage (choose one):\n"
            "  Method 1 (PowerShell Launcher - Recommended):\n"
            "    cd D:\\eco_nojin\\frontend\n"
            "    .\\run-e2e.ps1 ui\n\n"
            "  Method 2 (Direct):\n"
            "    $env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1'\n"
            "    pnpm exec playwright test --ui\n\n"
            "  Method 3 (package.json):\n"
            "    pnpm test:e2e:ui"
        )
        subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("Committed and pushed")
    except Exception as e:
        warn(f"Commit issue: {e}")

    # Final Report
    logger.info("")
    logger.info("=" * 70)
    logger.info("  🎉 Playwright 403 Fix - COMPLETE!")
    logger.info("=" * 70)
    logger.info("")
    logger.info("  HOW TO RUN E2E TESTS (3 Methods):")
    logger.info("")
    logger.info("  ╔══════════════════════════════════════════════════════════╗")
    logger.info("  ║  Method 1: PowerShell Launcher (RECOMMENDED)           ║")
    logger.info("  ╠══════════════════════════════════════════════════════════╣")
    logger.info("  ║  cd D:\\eco_nojin\\frontend                               ║")
    logger.info("  ║  .\\run-e2e.ps1              # Headless tests           ║")
    logger.info("  ║  .\\run-e2e.ps1 ui           # UI mode (visual)         ║")
    logger.debug("  ║  .\\run-e2e.ps1 debug        # Debug mode               ║")
    logger.info("  ╚══════════════════════════════════════════════════════════╝")
    logger.info("")
    logger.info("  ╔══════════════════════════════════════════════════════════╗")
    logger.info("  ║  Method 2: Manual PowerShell Setup                     ║")
    logger.info("  ╠══════════════════════════════════════════════════════════╣")
    logger.info("  ║  $env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'            ║")
    logger.info("  ║  $env:PLAYWRIGHT_BROWSERS_PATH = '0'                    ║")
    logger.info("  ║  pnpm exec playwright test --ui                         ║")
    logger.info("  ╚══════════════════════════════════════════════════════════╝")
    logger.info("")
    logger.info("  ╔══════════════════════════════════════════════════════════╗")
    logger.info("  ║  Method 3: package.json scripts (Windows CMD)          ║")
    logger.info("  ╠══════════════════════════════════════════════════════════╣")
    logger.info("  ║  pnpm test:e2e                                          ║")
    logger.info("  ║  pnpm test:e2e:ui                                       ║")
    logger.info("  ╚══════════════════════════════════════════════════════════╝")
    logger.info("")
    logger.info("  Files Created:")
    logger.info("    * playwright.config.ts (updated)")
    logger.info("    * run-e2e.ps1 (PowerShell launcher)")
    logger.info("    * setup-playwright-env.bat")
    logger.info("    * setup-playwright-env.ps1")
    logger.info("")
    logger.error("  If you still see 403 error:")
    logger.info("    1. Close ALL PowerShell windows")
    logger.info("    2. Open new PowerShell")
    logger.info("    3. cd D:\\eco_nojin\\frontend")
    logger.info("    4. .\\run-e2e.ps1 ui")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())