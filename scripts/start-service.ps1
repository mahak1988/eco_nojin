<#
.SYNOPSIS
Start the Eco Nojin API Gateway Windows Service.
#>
param(
    [string]$ServiceName = "EcoNojin-API"
)

$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Error "Service '$ServiceName' not found. Run .\scripts\install-service.ps1 first."
    exit 1
}

if ($service.Status -eq "Running") {
    Write-Host "Service '$ServiceName' is already running." -ForegroundColor Yellow
    exit 0
}

Write-Host "Starting service '$ServiceName'..."
Start-Service -Name $ServiceName

$timeout = 30
$elapsed = 0
while ((Get-Service -Name $ServiceName).Status -ne "Running" -and $elapsed -lt $timeout) {
    Start-Sleep -Seconds 1
    $elapsed++
}

$service = Get-Service -Name $ServiceName
if ($service.Status -eq "Running") {
    Write-Host "Service '$ServiceName' started successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "API available at: http://localhost:8000"
    Write-Host "Docs: http://localhost:8000/docs"
    Write-Host "Health: http://localhost:8000/health"
} else {
    Write-Error "Service failed to start within $timeout seconds. Check logs with .\scripts\service-logs.ps1"
    exit 1
}
