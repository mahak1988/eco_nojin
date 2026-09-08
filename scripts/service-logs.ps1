<#
.SYNOPSIS
Tail the API Gateway logs.
#>
param(
    [string]$ServiceName = "EcoNojin-API",
    [string]$LogPath = "D:\eco_nojin\logs\api-gateway.log"
)

if (-not (Test-Path $LogPath)) {
    Write-Host "Log file not found at: $LogPath" -ForegroundColor Yellow
    Write-Host "The service may not have started yet, or logs are in a different location." -ForegroundColor Yellow
    exit 1
}

Write-Host "Tailing logs from: $LogPath" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

Get-Content -Path $LogPath -Wait -Tail 50
