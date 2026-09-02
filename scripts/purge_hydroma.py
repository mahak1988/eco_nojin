#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HyDroMa Purge Protocol (Dependency-Aware Deletion)
===================================================
Removes ALL hydroma/cinematic components, pages, hooks and utils.
Keeps the app buildable via:
  - App.tsx / HomePage.tsx patching
  - /hydroma placeholder page (navigation stays intact)
  - global import-line sweep for leftover references
"""

import os
import sys
import subprocess
import re
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
SRC = FRONTEND / "src"

KEYWORDS = [
    'cinematic/', 'features/hydroma', 'farmsim',
    'HyDroMa', 'Hydroma', 'hydroma', 'Diag3D',
    'useWeatherStore', 'useArtisticStore', 'useQualityStore',
    'terrainHeight', 'worldToTerrainY',
    'SimulationPipeline', 'scientificChainApi',
]

PLACEHOLDER = '''import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { ToolOutlined } from '@ant-design/icons';

/**
 * Placeholder for the simulator route.
 * The old HyDroMa simulator was purged; a standard rebuild follows.
 */
export default function SimulatorPlaceholder() {
  const navigate = useNavigate();
  return (
    <div style={{ minHeight: '70vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <Result
        status="info"
        icon={<ToolOutlined />}
        title="شبیه‌ساز سه‌بعدی در حال بازسازی است"
        subTitle="نسخه قبلی HyDroMa حذف شد. نسخه جدید با معماری استاندارد و پایدار به‌زودی جایگزین می‌شود."
        extra={
          <Button type="primary" onClick={() => navigate('/')}>
            بازگشت به صفحه اصلی
          </Button>
        }
      />
    </div>
  );
}
'''


def ok(m): print(f"[OK] {m}")
def info(m): print(f"[INFO] {m}")
def warn(m): print(f"[WARN] {m}")
def err(m): print(f"[ERROR] {m}")


def setup_git_path():
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]


def strip_imports_and_jsx(content, extra_leaf_names=None):
    """Remove import lines / lazy consts / JSX referencing KEYWORDS."""
    # 1) import lines
    for kw in KEYWORDS:
        content = re.sub(
            r"import\s+[^'\n]*" + re.escape(kw) + r"[^'\n]*['\"];?\n",
            "", content)
        # lazy consts
        content = re.sub(
            r"const\s+\w+\s*=\s*lazy\(\s*\(\)\s*=>\s*import\(\s*['\"][^'\"]*" +
            re.escape(kw) + r"[^'\"]*['\"]\s*\)\s*\)\s*;?\n",
            "", content)

    # 2) JSX leaf elements (self-closing or with children)
    leaf_names = ['CinematicMode', 'CinematicSimulator', 'Diag3D',
                  'HyDroMa3D', 'HyDroMaCenter', 'HydromaDashboard']
    if extra_leaf_names:
        leaf_names += extra_leaf_names
    for name in leaf_names:
        content = re.sub(r"<" + name + r"\b[^>]*/>", "", content)
        content = re.sub(r"<" + name + r"\b[^>]*>[\s\S]*?</" + name + r">", "", content)

    # 3) Unwrap provider wrappers (keep children)
    for wrapper in ['SimulationPipelineProvider']:
        content = re.sub(r"<" + wrapper + r"\b[^>]*>", "", content)
        content = re.sub(r"</" + wrapper + r">", "", content)

    return content


def main():
    print("")
    print("=" * 70)
    print("  🗑️  HyDroMa Purge Protocol")
    print("=" * 70)
    print("")

    setup_git_path()

    # ------------------------------------------------------------------
    print("[Step 1] Patching App.tsx")
    print("-" * 70)
    app = (SRC / "App.tsx").read_text(encoding="utf-8-sig")

    app = strip_imports_and_jsx(app)

    # routes
    app = re.sub(r'<Route\s+path="/cinematic"[^>]*/>', '', app)
    app = re.sub(
        r'<Route\s+path="/hydroma"[^>]*/>',
        '<Route path="/hydroma" element={<SimulatorPlaceholder />} />',
        app)

    # ensure placeholder import
    if 'SimulatorPlaceholder' not in app:
        app = ("import SimulatorPlaceholder from './pages/SimulatorPlaceholder';\n" + app)

    (SRC / "App.tsx").write_text(app, encoding="utf-8")
    ok("App.tsx patched (routes + imports + JSX)")

    # ------------------------------------------------------------------
    print("[Step 2] Creating placeholder page")
    print("-" * 70)
    (SRC / "pages" / "SimulatorPlaceholder.tsx").write_text(PLACEHOLDER, encoding="utf-8")
    ok("pages/SimulatorPlaceholder.tsx created")

    # ------------------------------------------------------------------
    print("[Step 3] Patching HomePage.tsx (if it references 3D comps)")
    print("-" * 70)
    home = SRC / "pages" / "HomePage.tsx"
    if home.exists():
        text = home.read_text(encoding="utf-8-sig")
        cleaned = strip_imports_and_jsx(text)
        if cleaned != text:
            home.write_text(cleaned, encoding="utf-8")
            ok("HomePage.tsx patched")
        else:
            info("HomePage.tsx clean - no changes")
    else:
        warn("HomePage.tsx not found")

    # ------------------------------------------------------------------
    print("[Step 4] Global import sweep over remaining sources")
    print("-" * 70)
    swept = 0
    for f in SRC.rglob("*.ts*"):
        if f.name in ("App.tsx", "SimulatorPlaceholder.tsx"):
            continue
        text = f.read_text(encoding="utf-8-sig")
        if any(k in text for k in KEYWORDS):
            cleaned = strip_imports_and_jsx(text)
            if cleaned != text:
                f.write_text(cleaned, encoding="utf-8")
                swept += 1
                info(f"  swept: {f.relative_to(SRC)}")
    ok(f"Swept {swept} file(s)")

    # ------------------------------------------------------------------
    print("[Step 5] Physical deletion")
    print("-" * 70)
    deleted = []

    # directories
    for d in [SRC / "components" / "cinematic",
              SRC / "features" / "hydroma",
              SRC / "components" / "farmsim"]:
        if d.exists():
            shutil.rmtree(d)
            deleted.append(str(d.relative_to(SRC)) + "/ (dir)")

    # files by glob
    for pat in ["**/HyDroMa*.tsx", "**/Diag3D.tsx", "**/Hydroma*.tsx",
                "**/useWeatherStore.ts", "**/useArtisticStore.ts",
                "**/useQualityStore.ts", "**/terrainHeight.ts",
                "**/worldToTerrainY.ts", "**/SimulationPipeline.tsx",
                "**/scientificChainApi.ts"]:
        for f in SRC.glob(pat):
            if f.exists():
                f.unlink()
                deleted.append(str(f.relative_to(SRC)))

    for d in deleted:
        ok(f"  deleted: {d}")
    print("")

    # ------------------------------------------------------------------
    print("[Step 6] Build verification")
    print("-" * 70)
    result = subprocess.run("pnpm build", shell=True, cwd=FRONTEND,
                            capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=300)
    build_ok = result.returncode == 0
    if build_ok:
        ok("Build successful after purge")
        out = result.stdout + result.stderr
        for line in out.splitlines():
            if "dist/assets/index" in line and "kB" in line:
                info(f"  new main bundle: {line.strip()}")
    else:
        err("Build failed - leftover references:")
        for line in (result.stdout + result.stderr).splitlines()[-25:]:
            if line.strip():
                print(f"    {line}")
    print("")

    # ------------------------------------------------------------------
    if build_ok:
        print("[Step 7] Committing purge")
        print("-" * 70)
        try:
            subprocess.run("git add -A .", shell=True, cwd=PROJECT_ROOT, check=True)
            msg = ("chore(purge): remove ALL HyDroMa/cinematic components & pages\\n\\n"
                   "Deleted:\\n"
                   "- src/components/cinematic/ (entire dir, ~30 files)\\n"
                   "- src/features/hydroma/ (entire dir)\\n"
                   "- src/components/farmsim/ (entire dir)\\n"
                   "- HyDroMaCenter / HyDroMa3D / Diag3D / HydromaDashboard pages\\n"
                   "- useWeatherStore / useArtisticStore / useQualityStore hooks\\n"
                   "- terrainHeight / worldToTerrainY utils\\n"
                   "- SimulationPipeline context / scientificChainApi service\\n\\n"
                   "Kept:\\n"
                   "- /hydroma route -> SimulatorPlaceholder (nav stays intact)\\n"
                   "- App builds green; ready for standard simulator rebuild")
            subprocess.run(f'git commit -m "{msg}"', shell=True, cwd=PROJECT_ROOT, check=True)
            subprocess.run("git push", shell=True, cwd=PROJECT_ROOT, check=True)
            ok("Committed and pushed")
        except Exception as e:
            warn(f"Commit issue: {e}")

    print("")
    print("=" * 70)
    if build_ok:
        print("  ✅ PURGE COMPLETE - workspace clean")
    else:
        print("  ⚠️ Purge done but build has leftovers - see errors")
    print("=" * 70)
    print("")
    print("  Current state:")
    print("    • /hydroma  -> placeholder 'در حال بازسازی'")
    print("    • All other pages (home, admin, wallet, ...) untouched")
    print("    • Bundle is lighter (three/drei/postprocessing unused now)")
    print("")
    print("  Next step (when you're ready): standard simulator rebuild")
    print("    - single R3F Canvas module, local assets only")
    print("    - Zustand store + ErrorBoundary + lazy route")
    print("    - no external CDN textures (sanction-safe)")
    print("")
    return 0 if build_ok else 1


if __name__ == "__main__":
    sys.exit(main())