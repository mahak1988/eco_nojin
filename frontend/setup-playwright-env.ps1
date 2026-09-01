# Playwright Environment Setup for Iran (bypass CDN 403)

# Skip browser downloads completely
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'

# Force system Chrome usage
$env:PLAYWRIGHT_USE_SYSTEM_CHROME = 'true'

# Disable browser download checks
$env:PLAYWRIGHT_BROWSERS_PATH = '0'

Write-Host 'Playwright environment configured for system Chrome' -ForegroundColor Green
Write-Host 'Run: pnpm test:e2e or pnpm test:e2e:ui' -ForegroundColor Cyan
