#!/usr/bin/env python3
"""
Fix Vite Config for Vite 8 + Rolldown
======================================
Vite 8 uses Rolldown which has different syntax:
- import.meta.dirname instead of __dirname
- manualChunks must be a function
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
def err(m): print(f"\033[91m✗\033[0m  {m}")


# ═══════════════════════════════════════════════════════════════════════
# Vite 8 + Rolldown Compatible Config
# ═══════════════════════════════════════════════════════════════════════

VITE_CONFIG_FIXED = '''/**
 * Vite Configuration - Vite 8 + Rolldown Compatible
 * ==================================================
 * Optimizations:
 * - Manual chunks via function (Rolldown requirement)
 * - CSS code splitting
 * - Tree shaking
 * - Build optimization
 *
 * Vite 8 Changes:
 * - Use import.meta.dirname instead of __dirname
 * - manualChunks must be a function
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    // Bundle analyzer - only in analyze mode
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
    minify: 'esbuild',
    cssMinify: true,
    sourcemap: mode === 'development',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // Manual chunks via function (Rolldown requirement)
        manualChunks(id) {
          // Core React
          if (id.includes('node_modules/react') || 
              id.includes('node_modules/react-dom') || 
              id.includes('node_modules/react-router')) {
            return 'vendor-react';
          }

          // UI Libraries
          if (id.includes('node_modules/framer-motion') || 
              id.includes('node_modules/lucide-react') ||
              id.includes('node_modules/@radix-ui')) {
            return 'vendor-ui';
          }

          // Charts (heavy - separate chunk)
          if (id.includes('node_modules/recharts')) {
            return 'vendor-charts';
          }

          // 3D (very heavy - separate chunk)
          if (id.includes('node_modules/three') || 
              id.includes('node_modules/@react-three')) {
            return 'vendor-3d';
          }

          // Maps (heavy - separate chunk)
          if (id.includes('node_modules/leaflet') || 
              id.includes('node_modules/react-leaflet')) {
            return 'vendor-maps';
          }

          // i18n
          if (id.includes('node_modules/i18next') || 
              id.includes('node_modules/react-i18next')) {
            return 'vendor-i18n';
          }

          // React Query
          if (id.includes('node_modules/@tanstack/react-query')) {
            return 'vendor-query';
          }

          // Default chunk
          return undefined;
        },
        // Asset file names with hash for caching
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
      },
    },
    // Performance budget warnings
    chunkSizeWarningLimit: 500, // 500KB warning
  },

  // Optimize dependencies (pre-bundle for faster dev)
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
    print("\033[1m\033[96m  🔧 Fix Vite Config for Vite 8 + Rolldown\033[0m")
    print("\033[1m\033[96m" + "=" * 70 + "\033[0m\n")

    if not VITE_CONFIG.exists():
        err(f"فایل یافت نشد: {VITE_CONFIG}")
        return 1

    # Write fixed config
    info("نوشتن vite.config.ts اصلاح شده...")
    VITE_CONFIG.write_text(VITE_CONFIG_FIXED, encoding="utf-8")
    ok("vite.config.ts اصلاح شد")
    print()

    # Build
    info("اجرای build...")
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

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

    if result.returncode != 0:
        err("Build شکست خورد")
        output = result.stdout + result.stderr
        for line in output.splitlines()[-30:]:
            print(f"  {line}")
        return 1

    ok("Build موفق!")
    print()

    # Show bundle info
    info("Bundle chunks:")
    for line in result.stdout.splitlines():
        if "dist/assets/" in line or "built in" in line:
            print(f"  {line.strip()}")
    print()

    # Commit
    info("commit اصلاحات...")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(perf): fix vite config for Vite 8 + Rolldown"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        print(f"  ⚠ commit: {e}")

    print("\n\033[1m\033[92m" + "=" * 70 + "\033[0m")
    print("\033[1m\033[92m  🎉 Vite Config Fixed!\033[0m")
    print("\033[1m\033[92m" + "=" * 70 + "\033[0m\n")

    print("  Changes:")
    print("    ✓ import.meta.dirname (instead of __dirname)")
    print("    ✓ manualChunks as function (Rolldown requirement)")
    print("    ✓ Vendor chunks: react, ui, charts, 3d, maps, i18n, query")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())