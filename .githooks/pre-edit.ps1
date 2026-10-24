#!/usr/bin/env pwsh
<#
.SYNOPSIS
    v3.1 Rule-5 Quick Scan — the pre-edit gate for this repository.

.DESCRIPTION
    Runs the five cheap checks that keep the tree green, then prints either
    READY or NOT-READY and exits 0 or 1:

        1 guard     python tools/detect_imports.py --root .     (import guard)
        2 ruff      python -m ruff check . --statistics         (lint)
        3 unit      python -m pytest engine/tests -q -p no:cacheprovider
        4 services  python -m pytest services/  -q -p no:cacheprovider
        5 honesty   python tools/phantom_path_check.py          (no phantom cites)

    Every check is run with the repository root as the working directory and
    with $env:PYTHONPATH and $env:SECRET_KEY set (see AGENTS.md), so the hook
    works from a fresh shell with no environment prepared.

    The hook never modifies the working tree. It is a read-only gate: its whole
    purpose is to answer "is the tree green right now?" before an edit starts,
    because an edit made on a red tree cannot be proven behaviour-preserving.

.PARAMETER Quick
    Skip the slow half of the scan (the services suite). Use it inside an edit
    loop where the engine suite is the only thing that can plausibly have
    changed; the full scan still runs before every commit.

.PARAMETER RepoRoot
    Override the detected repository root. Defaults to the parent of this
    script's directory (.githooks/).

.EXAMPLE
    .githooks\pre-edit.ps1
    .githooks\pre-edit.ps1 -Quick
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Quick,
    [string]$RepoRoot
)

# Native commands write to stderr on purpose (pytest, ruff, the guard); that
# must not abort the hook, which checks $LASTEXITCODE itself.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

# ---------------------------------------------------------------------------
# Locating the repository and its interpreter
# ---------------------------------------------------------------------------

if ($RepoRoot) {
    $resolved = Resolve-Path -LiteralPath $RepoRoot -ErrorAction SilentlyContinue
    if (-not $resolved) { throw "RepoRoot does not exist: $RepoRoot" }
    $script:Root = $resolved.Path
}
else {
    $script:Root = (Get-Item -LiteralPath $PSScriptRoot).Parent.FullName
}

$script:Sibling = Split-Path -Parent $script:Root

function Get-WorkspaceInterpreter {
    <#
      The repo's own virtualenv when it exists, then the sibling venv documented
      in AGENTS.md (D:\eco_nojin\.venv), then python on PATH. A hook that
      silently falls back to the system interpreter measures a different Python
      than the suite, so the choice is printed with the result.
    #>
    $candidates = @(
        (Join-Path $script:Root '.venv\Scripts\python.exe'),
        (Join-Path $script:Root '.venv\bin\python'),
        (Join-Path $script:Sibling 'eco_nojin\.venv\Scripts\python.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }
    return 'python'
}

$script:Interpreter = Get-WorkspaceInterpreter

# ---------------------------------------------------------------------------
# Environment the suite expects (AGENTS.md)
# ---------------------------------------------------------------------------

$parts = @($script:Root)
$siblingRoot = Join-Path $script:Sibling 'eco_nojin'
if (Test-Path -LiteralPath $siblingRoot) { $parts += $siblingRoot }

$existing = @()
if ($env:PYTHONPATH) { $existing = $env:PYTHONPATH -split [IO.Path]::PathSeparator }
$missing = @($parts | Where-Object { $existing -notcontains $_ })
if ($missing.Count -gt 0) {
    $env:PYTHONPATH = (($missing + $existing) -join [IO.Path]::PathSeparator)
}
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = 'test-secret-key' }

# ---------------------------------------------------------------------------
# The five Quick-Scan commands
#
# ``Probe`` names a file that must exist for the check to be runnable; it is
# empty for the invocations that address a module rather than a script. A check
# whose probe is absent is reported as SKIPPED, never as a silent pass, so the
# READY line always says what was actually verified.
# ---------------------------------------------------------------------------

$script:Checks = @(
    @{
        Name   = 'guard'
        Title  = 'import guard'
        Detail = 'tools/detect_imports.py --root .'
        Args   = @('tools/detect_imports.py', '--root', '.')
        Probe  = 'tools/detect_imports.py'
        Slower = $false
    },
    @{
        Name   = 'ruff'
        Title  = 'ruff statistics (ratcheted, not zero)'
        Detail = 'ruff check . --statistics vs tools/lint_baseline.json'
        Args   = @('-m', 'ruff', 'check', '.', '--statistics')
        Probe  = ''
        Slower = $false
        Ratchet = $true
    },
    @{
        # B5: the ratchet was implemented only here, as an inline
        # ``Test-RuffBaseline``. The POSIX hook and CI did not enforce it, so
        # the debt could grow unnoticed. tools/check_lint_ratchet.py is the
        # single implementation all three entry points use.
        Name   = 'lintratchet'
        Title  = 'lint ratchet (the debt may only shrink)'
        Detail = 'tools/check_lint_ratchet.py --root .'
        Args   = @('tools/check_lint_ratchet.py', '--root', '.')
        Probe  = 'tools/check_lint_ratchet.py'
        Slower = $false
    },
    @{
        Name   = 'unit'
        Title  = 'engine unit suite'
        Detail = 'pytest engine/tests -q -p no:cacheprovider'
        Args   = @('-m', 'pytest', 'engine/tests', '-q', '-p', 'no:cacheprovider')
        Probe  = ''
        Slower = $false
    },
    @{
        Name   = 'services'
        Title  = 'services suite'
        Detail = 'pytest services/ -q -p no:cacheprovider'
        Args   = @('-m', 'pytest', 'services/', '-q', '-p', 'no:cacheprovider')
        Probe  = ''
        Slower = $true
    },
    @{
        Name   = 'honesty'
        Title  = 'phantom-path check (known families allowed)'
        Detail = 'pytest engine/tests/test_no_phantom_test_paths.py -q'
        Args   = @('-m', 'pytest', 'engine/tests/test_no_phantom_test_paths.py', '-q', '-p', 'no:cacheprovider')
        Probe  = 'engine/tests/test_no_phantom_test_paths.py'
        Slower = $false
    }
)

$script:Failures = New-Object System.Collections.ArrayList

function Get-RuffTotal([string[]]$Lines) {
    foreach ($line in $Lines) {
        if ($line -match 'Found\s+(\d+)\s+error') { return [int]$Matches[1] }
    }
    return $null
}

function Test-RuffBaseline([string[]]$Output, [double]$Elapsed) {
    <#
    The lint debt is recorded, not zero (769 on 2026-10-11; AGENTS.md documents the
    E501/B008/F401 debt as deliberately untouched). The Quick Scan therefore fails
    when the count RISES above the recorded baseline and passes at or below it --
    a ratchet, not a wish. Lowering the number in tools/lint_baseline.json is how
    the debt gets paid down.
    #>
    $baselinePath = Join-Path $script:Root 'tools\lint_baseline.json'
    if (-not (Test-Path -LiteralPath $baselinePath)) {
        Write-Host ("[ FAIL ] {0,-14} tools/lint_baseline.json missing (record the current debt first)" -f 'ruff')
        [void]$script:Failures.Add('ruff: no recorded lint baseline')
        return $true
    }
    $total = Get-RuffTotal -Lines $Output
    if ($null -eq $total) {
        Write-Host ("[ FAIL ] {0,-14} could not read the ruff total (is ruff installed?)" -f 'ruff')
        [void]$script:Failures.Add('ruff: unreadable total')
        return $true
    }
    $baseline = (Get-Content -LiteralPath $baselinePath -Raw | ConvertFrom-Json).rules.max_total
    if ($total -gt $baseline) {
        Write-Host ("[ FAIL ] {0,-14} lint total {1} is ABOVE the recorded baseline {2} (+{3})" -f `
            'ruff', $total, $baseline, ($total - $baseline))
        [void]$script:Failures.Add(("ruff: {0} > baseline {1}" -f $total, $baseline))
        return $true
    }
    Write-Host ("[ PASS ] {0,-14} {1} lint findings (baseline {2}, ratcheted)  ({3:N1}s)" -f `
        'ruff', $total, $baseline, $Elapsed)
    return $true
}

function Invoke-Scan([hashtable]$Check) {
    if ($Check.Slower -and $Quick) {
        Write-Host ("[ SKIP ] {0,-14} {1}" -f $Check.Name, $Check.Detail)
        return
    }
    if ($Check.Probe -and -not (Test-Path -LiteralPath (Join-Path $script:Root $Check.Probe))) {
        Write-Host ("[ SKIP ] {0,-14} {1} (not present in this tree)" -f `
            $Check.Name, $Check.Detail)
        return
    }
    $stopwatch = [Diagnostics.Stopwatch]::StartNew()
    Push-Location -LiteralPath $script:Root
    try {
        $output = & $script:Interpreter $Check.Args 2>&1
        $status = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    $stopwatch.Stop()

    # Trim the retained output so a failure shows what mattered.
    $lines = @()
    if ($null -ne $output) {
        $lines = @($output | ForEach-Object { "$_" })
    }

    if ($Check.Ratchet) {
        $ratchet = Test-RuffBaseline -Output $lines -Elapsed $stopwatch.Elapsed.TotalSeconds
        if ($ratchet) { return }
    }

    if ($status -eq 0) {
        Write-Host ("[ PASS ] {0,-14} {1}  ({2:N1}s)" -f `
            $Check.Name, $Check.Detail, $stopwatch.Elapsed.TotalSeconds)
        return
    }

    Write-Host ("[ FAIL ] {0,-14} {1}  (exit {2}, {3:N1}s)" -f `
        $Check.Name, $Check.Detail, $status, $stopwatch.Elapsed.TotalSeconds)
    [void]$script:Failures.Add(("{0}: {1}" -f $Check.Name, $Check.Detail))
    $tail = 25
    if ($lines.Count -gt 0) {
        $start = [Math]::Max(0, $lines.Count - $tail)
        Write-Host "         last output:"
        for ($index = $start; $index -lt $lines.Count; $index++) {
            if ($lines[$index]) { Write-Host ("           " + $lines[$index]) }
        }
    }
}

# ---------------------------------------------------------------------------
# Run the scan
# ---------------------------------------------------------------------------

Write-Host ("Rule-5 Quick Scan — repo {0}" -f $script:Root)
Write-Host ("interpreter: {0}" -f $script:Interpreter)
Write-Host ("PYTHONPATH : {0}" -f $env:PYTHONPATH)
if ($Quick) { Write-Host "mode       : quick (services suite skipped)" }
else { Write-Host "mode       : full" }
Write-Host ''

foreach ($check in $script:Checks) { Invoke-Scan $check }

Write-Host ''
if ($script:Failures.Count -eq 0) {
    Write-Host 'READY'
    exit 0
}

Write-Host "NOT-READY (failing: $($script:Failures -join '; '))"
exit 1
