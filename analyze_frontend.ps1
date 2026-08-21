Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "ECO NOJIN FRONTEND ANALYSIS REPORT" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# Find frontend directory
$frontendDirs = Get-ChildItem -Directory | Where-Object { 
    $_.Name -match "^(frontend|web|client|ui|app)$" 
}

if ($frontendDirs.Count -eq 0) {
    Write-Host "`n[WARNING] No frontend directory found at root level" -ForegroundColor Yellow
    Write-Host "Searching deeper..." -ForegroundColor Yellow
    $frontendDirs = Get-ChildItem -Directory -Recurse -Depth 2 | Where-Object { 
        $_.Name -match "^(frontend|web|client|ui|app|next)$" -and 
        $_.FullName -notmatch "node_modules|\.venv|dist|build" 
    } | Select-Object -First 3
}

foreach ($dir in $frontendDirs) {
    Write-Host "`n========================================================================" -ForegroundColor Cyan
    Write-Host "ANALYZING: $($dir.FullName)" -ForegroundColor Cyan
    Write-Host "========================================================================" -ForegroundColor Cyan

    # 1. package.json analysis
    Write-Host "`n[1] PACKAGE.JSON ANALYSIS" -ForegroundColor Yellow
    $pkg = Join-Path $dir.FullName "package.json"
    if (Test-Path $pkg) {
        $pkgContent = Get-Content $pkg -Raw | ConvertFrom-Json
        
        Write-Host "  Name: $($pkgContent.name)" -ForegroundColor Green
        Write-Host "  Version: $($pkgContent.version)" -ForegroundColor Green
        
        Write-Host "`n  FRAMEWORKS (dependencies):" -ForegroundColor Cyan
        $frameworks = @(
            "next", "react", "vue", "svelte", "angular", "nuxt",
            "typescript", "@remix-run/react", "astro", "vite"
        )
        foreach ($fw in $frameworks) {
            if ($pkgContent.dependencies.$fw -or $pkgContent.devDependencies.$fw) {
                $v = $pkgContent.dependencies.$fw
                if (-not $v) { $v = $pkgContent.devDependencies.$fw }
                Write-Host "    + $fw : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  UI LIBRARIES:" -ForegroundColor Cyan
        $uiLibs = @(
            "tailwindcss", "@mui/material", "antd", "@chakra-ui/react",
            "@shadcn/ui", "@radix-ui", "framer-motion", "bootstrap"
        )
        foreach ($lib in $uiLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  STATE MANAGEMENT:" -ForegroundColor Cyan
        $stateLibs = @(
            "redux", "@reduxjs/toolkit", "zustand", "mobx", "jotai",
            "recoil", "valtio", "@tanstack/react-query", "swr"
        )
        foreach ($lib in $stateLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  CHARTS & VISUALIZATION:" -ForegroundColor Cyan
        $chartLibs = @(
            "recharts", "chart.js", "d3", "victory", "nivo",
            "apexcharts", "react-chartjs-2", "frappe-charts"
        )
        foreach ($lib in $chartLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  FORMS & VALIDATION:" -ForegroundColor Cyan
        $formLibs = @(
            "react-hook-form", "formik", "yup", "zod", "@hookform/resolvers"
        )
        foreach ($lib in $formLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  I18N / LANGUAGES:" -ForegroundColor Cyan
        $i18nLibs = @("i18next", "react-i18next", "next-intl", "@lingui/core")
        foreach ($lib in $i18nLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  HTTP CLIENTS:" -ForegroundColor Cyan
        $httpLibs = @("axios", "@tanstack/react-query", "swr", "ky")
        foreach ($lib in $httpLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  MAPS:" -ForegroundColor Cyan
        $mapLibs = @("leaflet", "react-leaflet", "mapbox-gl", "react-map-gl", "@react-google-maps/api")
        foreach ($lib in $mapLibs) {
            if ($pkgContent.dependencies.$lib -or $pkgContent.devDependencies.$lib) {
                $v = $pkgContent.dependencies.$lib
                if (-not $v) { $v = $pkgContent.devDependencies.$lib }
                Write-Host "    + $lib : $v" -ForegroundColor Green
            }
        }

        Write-Host "`n  SCRIPTS:" -ForegroundColor Cyan
        foreach ($script in $pkgContent.scripts.PSObject.Properties) {
            Write-Host "    $($script.Name): $($script.Value)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  [NO package.json]" -ForegroundColor Red
    }

    # 2. Directory structure
    Write-Host "`n[2] DIRECTORY STRUCTURE (top 3 levels)" -ForegroundColor Yellow
    Get-ChildItem -Path $dir.FullName -Recurse -Directory -Depth 2 | 
        Where-Object { $_.FullName -notmatch "node_modules|\.next|dist|build|\.git" } |
        ForEach-Object {
            $relative = $_.FullName.Substring($dir.FullName.Length + 1)
            $indent = "  " * ($relative.Split([System.IO.Path]::DirectorySeparatorChar).Count - 1)
            Write-Host "  $indent+ $($_.Name)/" -ForegroundColor White
        }

    # 3. Key files
    Write-Host "`n[3] KEY CONFIGURATION FILES:" -ForegroundColor Yellow
    $keyFiles = @(
        "tsconfig.json", "jsconfig.json", "next.config.js", "next.config.mjs",
        "vite.config.ts", "vite.config.js", "tailwind.config.js", "tailwind.config.ts",
        "postcss.config.js", "postcss.config.cjs", ".env", ".env.local",
        "README.md", ".eslintrc.json", "eslint.config.js"
    )
    foreach ($file in $keyFiles) {
        $path = Join-Path $dir.FullName $file
        if (Test-Path $path) {
            $size = (Get-Item $path).Length
            Write-Host "  + $file ($size bytes)" -ForegroundColor Green
        }
    }

    # 4. Routing structure detection
    Write-Host "`n[4] ROUTING STRUCTURE:" -ForegroundColor Yellow
    $appDir = Join-Path $dir.FullName "app"
    $pagesDir = Join-Path $dir.FullName "pages"
    $srcPages = Join-Path $dir.FullName "src\pages"
    $srcApp = Join-Path $dir.FullName "src\app"

    if (Test-Path $appDir) {
        Write-Host "  Framework: Next.js 13+ App Router" -ForegroundColor Green
        Write-Host "  Root: $appDir"
    } elseif (Test-Path $pagesDir) {
        Write-Host "  Framework: Next.js Pages Router" -ForegroundColor Green
        Write-Host "  Root: $pagesDir"
    } elseif (Test-Path $srcPages) {
        Write-Host "  Framework: Next.js Pages Router (src layout)" -ForegroundColor Green
        Write-Host "  Root: $srcPages"
    } elseif (Test-Path $srcApp) {
        Write-Host "  Framework: Next.js 13+ App Router (src layout)" -ForegroundColor Green
        Write-Host "  Root: $srcApp"
    } else {
        Write-Host "  Framework: Unknown - check manually" -ForegroundColor Yellow
    }

    # 5. Sample pages/routes
    Write-Host "`n[5] EXISTING ROUTES/PAGES:" -ForegroundColor Yellow
    $routesDir = $null
    if (Test-Path $appDir) { $routesDir = $appDir }
    elseif (Test-Path $srcApp) { $routesDir = $srcApp }
    elseif (Test-Path $pagesDir) { $routesDir = $pagesDir }
    elseif (Test-Path $srcPages) { $routesDir = $srcPages }

    if ($routesDir) {
        $routeFiles = Get-ChildItem -Path $routesDir -Recurse -Include "page.tsx","page.jsx","page.ts","page.js","index.tsx","index.jsx","_app.tsx","layout.tsx" |
            Where-Object { $_.FullName -notmatch "node_modules" } |
            Select-Object -First 20
        
        foreach ($f in $routeFiles) {
            $rel = $f.FullName.Substring($routesDir.Length)
            $size = $f.Length
            Write-Host "  + $rel ($size bytes)" -ForegroundColor White
        }
    }

    # 6. Components count
    Write-Host "`n[6] COMPONENTS INVENTORY:" -ForegroundColor Yellow
    $compDirs = Get-ChildItem -Path $dir.FullName -Recurse -Directory | 
        Where-Object { $_.Name -match "^(components|ui|modules|features|widgets)$" -and $_.FullName -notmatch "node_modules" }
    
    $totalComponents = 0
    foreach ($cd in $compDirs) {
        $files = Get-ChildItem -Path $cd.FullName -Recurse -Include "*.tsx","*.jsx","*.vue","*.svelte" |
            Where-Object { $_.FullName -notmatch "node_modules" }
        $count = ($files | Measure-Object).Count
        $rel = $cd.FullName.Substring($dir.FullName.Length + 1)
        Write-Host "  + $rel : $count files" -ForegroundColor Cyan
        $totalComponents += $count
    }
    Write-Host "  Total: $totalComponents component files" -ForegroundColor Green

    # 7. API integration check
    Write-Host "`n[7] API INTEGRATION FILES:" -ForegroundColor Yellow
    $apiFiles = Get-ChildItem -Path $dir.FullName -Recurse -Include "*.ts","*.tsx","*.js","*.jsx" |
        Where-Object { 
            $_.FullName -notmatch "node_modules|\.next|dist|build" -and
            $_.Name -match "(api|client|http|axios|fetch|service)" -or
            $_.Directory.Name -match "^(api|services|lib|utils)$"
        } | Select-Object -First 15

    foreach ($f in $apiFiles) {
        $rel = $f.FullName.Substring($dir.FullName.Length + 1)
        Write-Host "  + $rel" -ForegroundColor Cyan
    }

    # 8. Check for existing platform/analysis code
    Write-Host "`n[8] PLATFORM-RELATED CODE (searching for 'analyze', 'platform'):" -ForegroundColor Yellow
    $platformFiles = Get-ChildItem -Path $dir.FullName -Recurse -Include "*.ts","*.tsx","*.js","*.jsx" |
        Where-Object { 
            $_.FullName -notmatch "node_modules|\.next|dist|build" -and
            $_.Length -lt 500000
        } | ForEach-Object {
            $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
            if ($content -match "platform/analyze|platform/landscapes|analyze_land|EcoNojin") {
                $_
            }
        } | Select-Object -First 10

    if ($platformFiles) {
        foreach ($f in $platformFiles) {
            $rel = $f.FullName.Substring($dir.FullName.Length + 1)
            Write-Host "  + $rel (contains platform code)" -ForegroundColor Magenta
        }
    } else {
        Write-Host "  No platform integration code found yet" -ForegroundColor Yellow
    }
}

Write-Host "`n========================================================================" -ForegroundColor Cyan
Write-Host "ANALYSIS COMPLETE" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "`nPlease send the FULL output of this command." -ForegroundColor Yellow
Write-Host "Based on this report, I will:" -ForegroundColor Yellow
Write-Host "  1. Respect the existing architecture" -ForegroundColor White
Write-Host "  2. Use the same UI libraries and patterns" -ForegroundColor White
Write-Host "  3. Extend (not replace) existing components" -ForegroundColor White
Write-Host "  4. Follow the same coding conventions" -ForegroundColor White
Write-Host "  5. Add only what is missing, never destroy" -ForegroundColor White
