<#
.SYNOPSIS
Stop the Eco Nojin API Gateway Windows Service.
#>
param(
    [string]$ServiceName = "EcoNojin-API"
)

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Error "Service '$ServiceName' not found."
    exit 1
}

if ($service.Status -eq "Stopped") {
    Write-Host "Service '$ServiceName' is already stopped." -ForegroundColor Yellow
    exit 0
}

Write-Host "Stopping service '$ServiceName'..."
Stop-Service -Name $ServiceName -Force

$timeout = 15
$elapsed = 0
while ((Get-Service -Name $ServiceName).Status -ne "Stopped" -and $elapsed -lt $timeout) {
    Start-Sleep -Seconds 1
    $elapsed++
}

$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Stopped") {
    Write-Host "Service '$ServiceName' stopped successfully." -ForegroundColor Green
} else {
    Write-Error "Service failed to stop within $timeout seconds."
    exit 1
}
