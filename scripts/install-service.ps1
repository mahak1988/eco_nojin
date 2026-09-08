<#
.SYNOPSIS
Install Eco Nojin API Gateway as a Windows Service using NSSM.

.DESCRIPTION
This script installs the FastAPI gateway as a Windows Service so it can start
automatically on boot and run without a logged-in console session.

.PARAMETER PythonPath
Full path to the Python 3.12 executable.

.PARAMETER WorkDir
Project root directory.

.PARAMETER ServiceName
Windows service name.
#>
param(
    [string]$PythonPath = "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe",
    [string]$WorkDir = "D:\eco_nojin",
    [string]$ServiceName = "EcoNojin-API"
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $WorkDir "logs"
$logPath = Join-Path $logDir "api-gateway.log"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Locate NSSM (Non-Sucking Service Manager)
$nssm = Get-Command nssm -ErrorAction SilentlyContinue
if (-not $nssm) {
    Write-Host "NSSM not found in PATH. Downloading..."
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = Join-Path $env:TEMP "nssm.zip"
    $nssmExtract = Join-Path $env:TEMP "nssm"

    if (-not (Test-Path $nssmExtract)) {
        New-Item -ItemType Directory -Path $nssmExtract -Force | Out-Null
    }

    Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
    Expand-Archive -Path $nssmZip -DestinationPath $nssmExtract -Force

    $nssmExe = Get-ChildItem $nssmExtract -Recurse -Filter "nssm.exe" | Select-Object -First 1
    if (-not $nssmExe) {
        throw "NSSM executable not found after extraction."
    }
    $nssmDir = Split-Path $nssmExe.FullName
    $env:PATH += ";$nssmDir"
    $nssm = Get-Command nssm -ErrorAction SilentlyContinue
}

Write-Host "Installing service '$ServiceName' using NSSM..."

# Remove existing service if present
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing service..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    & nssm remove $ServiceName confirm
}

# Install service
& nssm install $ServiceName $PythonPath "services.api_gateway.main:app" `
    "--app-dir" $WorkDir `
    "--host" "0.0.0.0" `
    "--port" "8000" `
    "--log-level" "info"

& nssm set $ServiceName AppDirectory $WorkDir
& nssm set $ServiceName AppStdout $logPath
& nssm set $ServiceName AppStderr $logPath
& nssm set $ServiceName AppParameters "-m uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8000 --log-level info"
& nssm set $ServiceName DisplayName "Eco Nojin API Gateway"
& nssm set $ServiceName Start SERVICE_AUTO_START
& nssm set $ServiceName ObjectName "LocalSystem"

Write-Host ""
Write-Host "Service installed successfully." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  .\scripts\start-service.ps1   - Start the service"
Write-Host "  .\scripts\stop-service.ps1    - Stop the service"
Write-Host "  .\scripts\service-status.ps1  - Check service status"
Write-Host "  .\scripts\service-logs.ps1    - View live logs"
Write-Host ""
Write-Host "Service will start automatically on Windows boot." -ForegroundColor Yellow
