<#
.SYNOPSIS
Install py-evm with retry logic and alternative mirrors.
#>
param(
    [string]$PythonPath = "D:\eco_nojin\.venv\Scripts\python.exe",
    [int]$MaxRetries = 5,
    [int]$RetryDelay = 10
)

$ErrorActionPreference = "Stop"

Write-Host "Installing py-evm (with retries)..." -ForegroundColor Cyan
Write-Host "Python: $PythonPath" -ForegroundColor Gray

$mirrors = @(
    "https://pypi.org/simple",
    "https://pypi.tuna.tsinghua.edu.cn/simple",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://mirrors.cloud.tencent.com/pypi/simple"
)

$attempt = 0
$installed = $false

while (-not $installed -and $attempt -lt $MaxRetries) {
    $attempt++
    Write-Host ""
    Write-Host "Attempt $attempt of $MaxRetries..." -ForegroundColor Yellow

    foreach ($mirror in $mirrors) {
        Write-Host "  Trying mirror: $mirror" -ForegroundColor Gray
        try {
            & $PythonPath -m pip install "eth-tester[py-evm]" --index-url $mirror --trusted-host $mirror --timeout 60 --retries 3
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Installed successfully from $mirror" -ForegroundColor Green
                $installed = $true
                break
            }
        } catch {
            Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        }
    }

    if (-not $installed -and $attempt -lt $MaxRetries) {
        Write-Host "  Waiting $RetryDelay seconds before retry..." -ForegroundColor Yellow
        Start-Sleep -Seconds $RetryDelay
    }
}

if (-not $installed) {
    Write-Host ""
    Write-Error "Failed to install py-evm after $MaxRetries attempts. Check your network connection."
    exit 1
}

Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Cyan
& $PythonPath -c "from eth_tester import EthereumTester, PyEVMBackend; print('✓ py-evm working')"

Write-Host ""
Write-Host "Done! You can now run blockchain tests." -ForegroundColor Green
