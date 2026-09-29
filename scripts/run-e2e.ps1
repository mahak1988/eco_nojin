param(
  [Parameter(Mandatory = $true)][string[]]$Spec
)

# Run the E2E suite against a production build, with the server owned by this
# script.
#
# The tracked background process was reaped between tool calls, so a long
# Playwright run lost its server part-way and the suite collapsed to a handful of
# passes. Everything now lives in one process: start, wait for readiness, run,
# stop. The server is a PowerShell job rather than a child process so the shell
# does not stay attached to it.

$ErrorActionPreference = 'Stop'
$web = 'D:\eco_nojin\apps\web'
Set-Location $web

# Anything already on the port would be a stale build.
$existing = (Get-NetTCPConnection -LocalPort 3001 -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($existing) {
  Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
}

$serverLog = Join-Path $env:TEMP 'e2e-server.log'
$server = Start-Process -FilePath 'node_modules\.bin\next.cmd' `
  -ArgumentList 'start', '-p', '3001' `
  -WorkingDirectory $web `
  -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput $serverLog `
  -RedirectStandardError "$serverLog.err"

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 1
  try {
    $probe = Invoke-WebRequest -Uri 'http://localhost:3001/fa/home' -UseBasicParsing -TimeoutSec 5
    if ($probe.StatusCode -eq 200) { $ready = $true; break }
  } catch {
    # not up yet
  }
}

if (-not $ready) {
  Write-Output 'server did not become ready'
  Get-Content "$serverLog.err" -ErrorAction SilentlyContinue | Select-Object -Last 10
  Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
  exit 1
}

Write-Output "server ready (pid $($server.Id))"
Write-Output "specs: $($Spec -join ', ')"
Write-Output ''

try {
  & node_modules\.bin\playwright.cmd test @Spec --project='Mobile Safari' --reporter=line
  $code = $LASTEXITCODE
} finally {
  Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
}

exit $code
