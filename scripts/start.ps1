<#
.SYNOPSIS
Run the API Gateway directly without Windows Service (for development).
#>
param(
    [string]$WorkDir = "D:\eco_nojin",
    [string]$PythonPath = "D:\eco_nojin\.venv\Scripts\python.exe",
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0"
)

$logDir = Join-Path $WorkDir "logs"
$logPath = Join-Path $logDir "api-gateway-dev.log"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Set-Location $WorkDir

Write-Host "Starting API Gateway in development mode..." -ForegroundColor Green
Write-Host "  Host: $Host" -ForegroundColor Cyan
Write-Host "  Port: $Port" -ForegroundColor Cyan
Write-Host "  Logs: $logPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

& $PythonPath -m uvicorn services.api_gateway.main:app --host $Host --port $Port --reload --log-level info 2>&1 | Tee-Object -FilePath $logPath
