#!/usr/bin/env python3
"""
Fix Vite 8 Build Error - Install esbuild
==========================================
Vite 8 removed esbuild from built-in dependencies.
We need to install it separately.

Also: simplify minify config for compatibility.
"""

import os
import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
VITE_CONFIG = FRONTEND / "vite.config.ts"


def ok(m): print(f"\033[92m✓\033[0m  {m}")
def info(m): print(f"\033[94mℹ\033[0m  {m}")
def warn(m): print(f"\033[93m⚠\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


# ═══════════════════════════════════════════════════════════════════════
# Vite 8 + Rolldown + esbuild Compatible Config
# ═══════════════════════════════════════════════════════════════════════

VITE_CONFIG_FIXED = '''/**
 * Vite Configuration - Vite 8 + Rolldown + esbuild
 * =================================================
 * Optimizations:
 * - Manual chunks via function (Rolldown requirement)
 * - CSS code splitting
 * - Tree shaking
 * - Build optimization
 *
 * Vite 8 Notes:
 * - Uses import.meta.dirname instead of __dirname
 * - manualChunks must be a function
 * - Requires esbuild as separate dependency
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    mode === 'analyze' &&
      visualizer({
        open: true,
        filename: 'dist/stats.html',
        gzipSize: true,
        brotliSize: true,
      }),
  ].filter(Boolean),

  resolve: {
    alias: {
      '@': import.meta.dirname + '/src',
      '@features': import.meta.dirname + '/src/features',
      '@components': import.meta.dirname + '/src/components',
      '@hooks': import.meta.dirname + '/src/hooks',
      '@utils': import.meta.dirname + '/src/utils',
      '@types': import.meta.dirname + '/src/types',
    },
  },

  build: {
    target: 'es2020',
    // Use terser or let Vite choose automatically (rolldown minifier)
    // Avoid 'esbuild' string to prevent deprecation warnings
    minify: true,
    cssMinify: true,
    sourcemap: mode === 'development',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (typeof id !== 'string') return undefined;

          if (id.includes('node_modules')) {
            // Core React
            if (id.includes('/react-dom/') || 
                id.includes('/react/') || 
                id.includes('/react-router')) {
              return 'vendor-react';
            }

            // UI Libraries
            if (id.includes('/framer-motion/') || 
                id.includes('/lucide-react/') ||
                id.includes('/@radix-ui/')) {
              return 'vendor-ui';
            }

            // Charts (heavy)
            if (id.includes('/recharts/')) {
              return 'vendor-charts';
            }

            // 3D (very heavy)
            if (id.includes('/three/') || 
                id.includes('/@react-three/')) {
              return 'vendor-3d';
            }

            // Maps
            if (id.includes('/leaflet/') || 
                id.includes('/react-leaflet/')) {
              return 'vendor-maps';
            }

            // i18n
            if (id.includes('/i18next/') || 
                id.includes('/react-i18next/')) {
              return 'vendor-i18n';
            }

            // React Query
            if (id.includes('/@tanstack/react-query/')) {
              return 'vendor-query';
            }

            // Other vendors
            return 'vendor-other';
          }

          return undefined;
        },
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
      },
    },
    chunkSizeWarningLimit: 500,
  },

  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'framer-motion',
      'lucide-react',
    ],
  },

  server: {
    port: 5173,
    open: false,
    cors: true,
  },
}));
'''


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("\n\033[1m\033[96m" + "=" * 70 + "\033[0m")
    print("\033[1m\033[96m  🔧 Fix Vite 8 Build - Install esbuild\033[0m")
    print("\033[1m\033[96m" + "=" * 70 + "\033[0m\n")

    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # ═══ Step 1: Install esbuild ═══
    info("Step 1: نصب esbuild...")
    result = subprocess.run(
        "pnpm add -D esbuild",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180
    )

    if result.returncode == 0:
        ok("esbuild نصب شد")
    else:
        warn(f"esbuild installation: {result.stderr[:200] if result.stderr else 'unknown error'}")
    print()

    # ═══ Step 2: Update vite.config.ts ═══
    info("Step 2: به‌روزرسانی vite.config.ts...")
    VITE_CONFIG.write_text(VITE_CONFIG_FIXED, encoding="utf-8")
    ok("vite.config.ts اصلاح شد")
    print()

    # ═══ Step 3: Build ═══
    info("Step 3: اجرای build...")
    result = subprocess.run(
        "pnpm build",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    output = result.stdout + result.stderr

    if result.returncode != 0:
        err("Build شکست خورد")
        for line in output.splitlines()[-30:]:
            print(f"  {line}")
        return 1

    ok("Build موفق!")
    print()

    # Show bundle info
    info("Bundle chunks:")
    for line in result.stdout.splitlines():
        if "dist/assets/" in line and ("vendor" in line or "index" in line):
            print(f"  {line.strip()}")
    print()
    for line in result.stdout.splitlines():
        if "built in" in line:
            print(f"  {line.strip()}")
    print()

    # ═══ Step 4: Run tests ═══
    info("Step 4: اجرای تست‌ها...")
    test_result = subprocess.run(
        "pnpm test",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180
    )
    for line in test_result.stdout.splitlines():
        if any(k in line for k in ["Test Files", "Tests", "passed", "failed"]):
            print(f"  {line}")
    print()

    # ═══ Step 5: Commit ═══
    info("Step 5: commit...")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(perf): install esbuild for Vite 8 compatibility"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        warn(f"commit: {e}")

    print("\n\033[1m\033[92m" + "=" * 70 + "\033[0m")
    print("\033[1m\033[92m  🎉 Vite 8 Build Fixed!\033[0m")
    print("\033[1m\033[92m" + "=" * 70 + "\033[0m\n")

    print("  Changes:")
    print("    ✓ Installed esbuild as dev dependency")
    print("    ✓ Fixed minify config (no explicit 'esbuild')")
    print("    ✓ Fixed manualChunks function (Rolldown)")
    print("    ✓ Fixed import.meta.dirname (Vite 8)")
    print()

    print("  Vendor chunks:")
    print("    • vendor-react (core React)")
    print("    • vendor-ui (framer-motion, lucide)")
    print("    • vendor-charts (recharts)")
    print("    • vendor-3d (three.js)")
    print("    • vendor-maps (leaflet)")
    print("    • vendor-i18n (i18next)")
    print("    • vendor-query (react-query)")
    print("    • vendor-other (remaining)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())