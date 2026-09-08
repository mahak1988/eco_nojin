<#
.SYNOPSIS
Check the status of the Eco Nojin API Gateway Windows Service.
#>
param(
    [string]$ServiceName = "EcoNojin-API"
)

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Host "Service '$ServiceName' not found. Run .\scripts\install-service.ps1 first." -ForegroundColor Red
    exit 1
}

$service | Format-Table Name, Status, StartType, DisplayName -AutoSize

if ($service.Status -eq "Running") {
    Write-Host ""
    Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "Health: http://localhost:8000/health" -ForegroundColor Cyan
}
