#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redesign_final.py — complete rewrite: lazy routes + tokens, prove-then-push.

Self-contained. Assumes nothing about previous script versions.
  1. verify web router integrity
  2. write tokens.css + wire into ui/index.ts (idempotent)
  3. write the FINAL lazy.tsx (named-export aware, bracket access)
  4. verify dashboard router already uses lazyPage (no rewrite needed)
  5. build (full pnpm path) — must pass
  6. chunk census
  7. tokens-in-css check
  8. commit + push
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\eco_nojin")
FRONT = ROOT / "frontend"
DASH_APP = FRONT / "apps" / "dashboard" / "src" / "app"
UI_SRC = FRONT / "packages" / "ui" / "src"
GIT = r"C:\Program Files\Git\cmd\git.exe"

print("script start", flush=True)

TOKENS_CSS = """/* eco_nojin design tokens - Nature Distilled palette */
:root {
  --eco-color-primary: #4A6741;
  --eco-color-primary-deep: #2D5016;
  --eco-color-primary-soft: #E8F0E5;
  --eco-color-accent: #D4A373;
  --eco-color-accent-soft: #F6EDE2;
  --eco-color-bg: #F4F1EA;
  --eco-color-surface: #FFFFFF;
  --eco-color-surface-muted: #EDE9E0;
  --eco-color-border: #DDD8CC;
  --eco-color-ink: #1F2820;
  --eco-color-ink-subtle: #5C6657;
  --eco-color-ink-faint: #8A937F;
  --eco-color-success: #3E7A3E;
  --eco-color-warning: #B8860B;
  --eco-color-danger: #9C3A2E;
  --eco-color-info: #3A6B8C;
  --eco-space-1: .25rem;
  --eco-space-2: .5rem;
  --eco-space-4: 1rem;
  --eco-space-6: 1.5rem;
  --eco-space-8: 2rem;
  --eco-space-12: 3rem;
  --eco-font-sans: "Inter", "Vazirmatn", system-ui, sans-serif;
  --eco-font-serif: "Playfair Display", "Amiri", serif;
  --eco-radius-md: 10px;
  --eco-radius-lg: 16px;
  --eco-shadow-1: 0 1px 3px rgb(31 40 32 / .08);
  --eco-shadow-2: 0 4px 14px rgb(31 40 32 / .12);
  --eco-ease: cubic-bezier(.22, 1, .36, 1);
}
.dark {
  --eco-color-bg: #171B15;
  --eco-color-surface: #20261E;
  --eco-color-surface-muted: #2A3126;
  --eco-color-border: #3A4436;
  --eco-color-ink: #E9EDE6;
  --eco-color-ink-subtle: #B4BBAE;
  --eco-color-ink-faint: #7E8674;
}
"""

LAZY_TS = """import { Suspense, lazy, type ComponentType, type ReactElement } from 'react';
import { Spinner } from '@eco/ui';

/**
 * Route-level code-splitting helper.
 * Supports default exports, explicit named exports, and auto-detection
 * (prefers an export ending in "Page", else the first PascalCase function).
 */
export function lazyPage(
  load: () => Promise<Record<string, unknown>>,
  named?: string,
): () => ReactElement {
  const C = lazy(async () => {
    const mod = await load();

    let comp: unknown = named ? mod[named] : mod['default'];

    if (typeof comp !== 'function' && !named) {
      const candidates = Object.keys(mod).filter(
        (k) => k !== 'default' && /^[A-Z]/.test(k) && typeof mod[k] === 'function',
      );
      const pick = candidates.find((k) => k.endsWith('Page')) ?? candidates[0];
      comp = pick ? mod[pick] : undefined;
    }

    if (typeof comp !== 'function') {
      throw new Error(
        named
          ? 'lazyPage: export "' + named + '" not found in module'
          : 'lazyPage: no default export and no component-like export found',
      );
    }

    return { default: comp as ComponentType };
  });

  function LazyRoute(): ReactElement {
    return (
      <Suspense
        fallback={
          <div className="flex min-h-[60vh] items-center justify-center">
            <Spinner size="lg" />
          </div>
        }
      >
        <C />
      </Suspense>
    );
  }

  return LazyRoute;
}
"""


def git(*args):
    return subprocess.run([GIT, *args], cwd=str(ROOT), capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def main():
    print("[1] web router integrity", flush=True)
    web_router = FRONT / "apps" / "web" / "src" / "app" / "router.tsx"
    wt = web_router.read_text(encoding="utf-8", errors="replace")
    if "createRouter({" not in wt:
        print("    web router.tsx TRUNCATED — abort", flush=True)
        return 1
    print("    OK", flush=True)

    print("[2] tokens.css + wiring", flush=True)
    tokens = UI_SRC / "tokens.css"
    tokens.write_text(TOKENS_CSS, encoding="utf-8", newline="\n")
    idx = UI_SRC / "index.ts"
    t = idx.read_text(encoding="utf-8")
    if "tokens.css" not in t:
        t = "import './tokens.css'\n" + t
        idx.write_text(t, encoding="utf-8")
        print("    tokens written + wired", flush=True)
    else:
        print("    tokens already wired (rewritten anyway)", flush=True)

    print("[3] lazy.tsx (FINAL version)", flush=True)
    lazy_file = DASH_APP / "lazy.tsx"
    lazy_file.write_text(LAZY_TS, encoding="utf-8", newline="\n")
    print("    written", flush=True)

    print("[4] dashboard router state check", flush=True)
    router = DASH_APP / "router.tsx"
    rt = router.read_text(encoding="utf-8", errors="replace")
    n_lazy = rt.count("lazyPage(")
    n_imports = len(re.findall(r"import \{ \w+Page \} from '@/features/", rt))
    print(f"    lazyPage calls: {n_lazy} | old-style imports left: {n_imports}",
          flush=True)
    if n_lazy < 25:
        print("    WARNING: fewer lazy calls than expected — check router",
              flush=True)

    print("[5] BUILD (this is the proof)", flush=True)
    pnpm = shutil.which("pnpm")
    if not pnpm:
        print("    pnpm not found on PATH", flush=True)
        return 1
    r = subprocess.run([pnpm, "-C", "frontend", "build"],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1500)
    combined = (r.stdout or "") + (r.stderr or "")
    lines = [l for l in combined.splitlines() if l.strip()]
    for l in lines[-30:]:
        print("  " + l[:170], flush=True)
    print(f"  build exit={r.returncode}", flush=True)
    if r.returncode != 0:
        print("BUILD FAILED — nothing committed", flush=True)
        return 1

    print("[6] chunk census", flush=True)
    assets = FRONT / "apps" / "dashboard" / "dist" / "assets"
    js = sorted(assets.glob("*.js"), key=lambda p: p.stat().st_size,
                reverse=True)
    print(f"  dashboard JS chunks: {len(js)}", flush=True)
    for c in js[:8]:
        print(f"    {c.stat().st_size // 1024:5d} KB  {c.name}", flush=True)

    print("[7] tokens in built css", flush=True)
    found = []
    for css in (FRONT / "apps").rglob("dist/assets/*.css"):
        if "--eco-color-primary" in css.read_text(encoding="utf-8",
                                                  errors="replace"):
            found.append(str(css.relative_to(FRONT)))
    if found:
        for f in found:
            print(f"    tokens present: {f}", flush=True)
    else:
        print("    tokens NOT in built css (wiring issue)", flush=True)

    print("[8] commit + push", flush=True)
    git("add", "--",
        "frontend/apps/dashboard/src/app/lazy.tsx",
        "frontend/apps/dashboard/src/app/router.tsx",
        "frontend/packages/ui/src/tokens.css",
        "frontend/packages/ui/src/index.ts")
    c = git("commit", "-m",
            "feat(frontend): route-level code splitting + Nature Distilled "
            "design tokens; lazyPage helper supports named exports")
    print(f"  commit rc={c.returncode}", flush=True)
    if c.returncode == 0:
        p = git("push", "origin", "main")
        print(f"  push rc={p.returncode}", flush=True)

    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())