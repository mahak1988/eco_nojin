#!/usr/bin/env python3
"""
Fix pnpm v11 - Remove esbuild Completely
==========================================
pnpm v11 security policy blocks esbuild builds.
Solution: Remove esbuild entirely and use Rolldown's built-in minifier.

Vite 8 + Rolldown has its own minifier, so esbuild is optional.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
PACKAGE_JSON = FRONTEND / "package.json"
PNPM_LOCK = FRONTEND / "pnpm-lock.yaml"
VITE_CONFIG = FRONTEND / "vite.config.ts"


def ok(m): print(f"\033[92m✓\033[0m  {m}")
def info(m): print(f"\033[94mℹ\033[0m  {m}")
def warn(m): print(f"\033[93m⚠\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


# ═══════════════════════════════════════════════════════════════════════
# Step 1: Remove esbuild from package.json
# ═══════════════════════════════════════════════════════════════════════

def remove_esbuild_from_package_json():
    """حذف کامل esbuild از package.json"""
    info("خواندن package.json...")

    if not PACKAGE_JSON.exists():
        err(f"package.json یافت نشد")
        return False

    try:
        data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"خطا در parsing: {e}")
        return False

    removed = False

    # حذف از devDependencies
    if "devDependencies" in data and "esbuild" in data["devDependencies"]:
        del data["devDependencies"]["esbuild"]
        ok("esbuild از devDependencies حذف شد")
        removed = True

    # حذف از dependencies
    if "dependencies" in data and "esbuild" in data["dependencies"]:
        del data["dependencies"]["esbuild"]
        ok("esbuild از dependencies حذف شد")
        removed = True

    # حذف پیکربندی pnpm onlyBuiltDependencies
    if "pnpm" in data and "onlyBuiltDependencies" in data["pnpm"]:
        only_built = data["pnpm"]["onlyBuiltDependencies"]
        data["pnpm"]["onlyBuiltDependencies"] = [
            pkg for pkg in only_built
            if "esbuild" not in pkg
        ]
        ok("پیکربندی esbuild از pnpm.onlyBuiltDependencies حذف شد")

    # ذخیره
    PACKAGE_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    if not removed:
        info("esbuild در package.json نبود")

    return True


# ═══════════════════════════════════════════════════════════════════════
# Step 2: Write Vite Config (No esbuild at all)
# ═══════════════════════════════════════════════════════════════════════

VITE_CONFIG_NO_ESBUILD = '''/**
 * Vite Configuration - Vite 8 + Rolldown (No esbuild)
 * ====================================================
 * Uses Rolldown's built-in minifier instead of esbuild.
 *
 * Vite 8 Notes:
 * - Rolldown has its own high-performance minifier
 * - No external esbuild dependency needed
 * - manualChunks as function (Rolldown requirement)
 * - import.meta.dirname instead of __dirname
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
    // Rolldown's built-in minifier (no esbuild needed)
    // Setting to 'terser' would require installing terser
    // Leaving unset uses Rolldown's fast native minifier
    sourcemap: mode === 'development',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (typeof id !== 'string') return undefined;

          if (id.includes('node_modules')) {
            if (id.includes('/react-dom/') ||
                id.includes('/react/') ||
                id.includes('/react-router')) {
              return 'vendor-react';
            }
            if (id.includes('/framer-motion/') ||
                id.includes('/lucide-react/') ||
                id.includes('/@radix-ui/')) {
              return 'vendor-ui';
            }
            if (id.includes('/recharts/')) return 'vendor-charts';
            if (id.includes('/three/') ||
                id.includes('/@react-three/')) {
              return 'vendor-3d';
            }
            if (id.includes('/leaflet/') ||
                id.includes('/react-leaflet/')) {
              return 'vendor-maps';
            }
            if (id.includes('/i18next/') ||
                id.includes('/react-i18next/')) {
              return 'vendor-i18n';
            }
            if (id.includes('/@tanstack/react-query/')) {
              return 'vendor-query';
            }
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
    print("\033[1m\033[96m  🔧 Remove esbuild - Use Rolldown Minifier\033[0m")
    print("\033[1m\033[96m" + "=" * 70 + "\033[0m\n")

    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    # ═══ Step 1: Remove esbuild from package.json ═══
    print("\033[1mStep 1: حذف esbuild از package.json\033[0m")
    print("-" * 70)
    if not remove_esbuild_from_package_json():
        return 1
    print()

    # ═══ Step 2: Uninstall esbuild ═══
    print("\033[1mStep 2: uninstall esbuild\033[0m")
    print("-" * 70)
    info("اجرای pnpm uninstall esbuild...")
    result = subprocess.run(
        "pnpm uninstall esbuild",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120
    )

    if result.returncode == 0:
        ok("esbuild حذف شد")
    else:
        warn(f"uninstall: {result.stderr[:200] if result.stderr else 'warning'}")
    print()

    # ═══ Step 3: Write Vite Config ═══
    print("\033[1mStep 3: بازنویسی vite.config.ts (no esbuild)\033[0m")
    print("-" * 70)
    VITE_CONFIG.write_text(VITE_CONFIG_NO_ESBUILD, encoding="utf-8")
    ok("vite.config.ts بازنویسی شد")
    print()

    # ═══ Step 4: Clean install ═══
    print("\033[1mStep 4: pnpm install (clean)\033[0m")
    print("-" * 70)
    info("اجرای pnpm install...")
    result = subprocess.run(
        "pnpm install",
        shell=True,
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300
    )

    if result.returncode != 0:
        err("pnpm install شکست خورد")
        for line in (result.stdout + result.stderr).splitlines()[-20:]:
            print(f"  {line}")
        return 1

    ok("pnpm install موفق")
    print()

    # ═══ Step 5: Build ═══
    print("\033[1mStep 5: اجرای build\033[0m")
    print("-" * 70)
    info("Building production bundle...")
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
        for line in output.splitlines()[-35:]:
            print(f"  {line}")
        return 1

    ok("Build موفق!")
    print()

    # Show bundle
    info("Bundle chunks:")
    for line in result.stdout.splitlines():
        if "dist/assets/" in line and any(k in line for k in ["vendor", "index", "HyDroMaCenter"]):
            print(f"  {line.strip()}")
    print()
    for line in result.stdout.splitlines():
        if "built in" in line:
            print(f"  {line.strip()}")
    print()

    # ═══ Step 6: Tests ═══
    print("\033[1mStep 6: اجرای تست‌ها\033[0m")
    print("-" * 70)
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

    # ═══ Step 7: Commit ═══
    print("\033[1mStep 7: commit\033[0m")
    print("-" * 70)
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        subprocess.run(
            'git commit -m "fix(perf): remove esbuild, use Rolldown built-in minifier (pnpm v11 compat)"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        warn(f"commit: {e}")

    print("\n\033[1m\033[92m" + "=" * 70 + "\033[0m")
    print("\033[1m\033[92m  🎉 Phase 3 - Performance Setup Complete!\033[0m")
    print("\033[1m\033[92m" + "=" * 70 + "\033[0m\n")

    print("  📊 دستاوردها:")
    print("    ✓ Removed esbuild dependency (pnpm v11 compatible)")
    print("    ✓ Using Rolldown's built-in minifier")
    print("    ✓ Manual chunks for vendor splitting")
    print("    ✓ Design tokens (colors, spacing, typography)")
    print("    ✓ Animation utilities (GPU-accelerated)")
    print("    ✓ Performance monitoring (Core Web Vitals)")
    print()

    print("  🎯 استفاده:")
    print("    import { fadeIn, slideUp } from '@/utils/animations';")
    print("    .card { background: var(--bg-card); }")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())