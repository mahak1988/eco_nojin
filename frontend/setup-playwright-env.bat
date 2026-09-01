@echo off
REM Playwright Environment Setup for Iran (bypass CDN 403)

REM Skip browser downloads completely
set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

REM Force system Chrome usage
set PLAYWRIGHT_USE_SYSTEM_CHROME=true

REM Disable browser download checks
set PLAYWRIGHT_BROWSERS_PATH=0

echo Playwright environment configured for system Chrome
echo Run: pnpm test:e2e or pnpm test:e2e:ui
