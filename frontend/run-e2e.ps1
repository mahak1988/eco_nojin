# Playwright E2E Test Launcher (PowerShell)
# This script sets env vars and runs E2E tests

# Set environment variables for current session
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'
$env:PLAYWRIGHT_BROWSERS_PATH = '0'
$env:PLAYWRIGHT_USE_SYSTEM_CHROME = 'true'

Write-Host '==================================' -ForegroundColor Cyan
Write-Host '  Playwright E2E Test Launcher' -ForegroundColor Cyan
Write-Host '==================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Environment configured:' -ForegroundColor Green
Write-Host '  - PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = 1' -ForegroundColor Yellow
Write-Host '  - PLAYWRIGHT_BROWSERS_PATH = 0' -ForegroundColor Yellow
Write-Host '  - PLAYWRIGHT_USE_SYSTEM_CHROME = true' -ForegroundColor Yellow
Write-Host ''

# Determine what to run
$testMode = $args[0]

switch ($testMode) {
    'ui' {
        Write-Host 'Running: playwright test --ui' -ForegroundColor Green
        pnpm exec playwright test --ui
    }
    'debug' {
        Write-Host 'Running: playwright test --debug' -ForegroundColor Green
        pnpm exec playwright test --debug
    }
    'report' {
        Write-Host 'Running: playwright show-report' -ForegroundColor Green
        pnpm exec playwright show-report
    }
    default {
        Write-Host 'Running: playwright test (headless)' -ForegroundColor Green
        pnpm exec playwright test
    }
}
