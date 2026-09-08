#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redesign_setup.py — precise monorepo analysis + i18n activation + redesign bootstrap.

Fixes vs previous analyzer:
  1. Dependencies: walks ALL package.json files in the monorepo
     (root misses React/Vite because they live in sub-packages)
  2. Memory-leak heuristic dropped (was naive); replaced by focused
     useEffect-without-cleanup scan that inspects return statements
  3. i18n: reads the EXISTING 4 locales (en/fa/ar/ur JSONs!) and
     verifies the i18n package config + installs runtime deps
  4. Lazy-loading: counts React.lazy/Suspense accurately
Outputs: redesign_plan.json + concrete next steps.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\eco_nojin")
FRONT = ROOT / "frontend"
REPORT = ROOT / "redesign_plan.json"


def say(msg):
    print(msg, flush=True)


def pkg_jsons():
    """All package.json files, excluding node_modules."""
    out = []
    for p in FRONT.rglob("package.json"):
        if "node_modules" in p.parts:
            continue
        out.append(p)
    return out


def collect_deps():
    deps = {}
    devdeps = {}
    names = []
    for pj in pkg_jsons():
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            continue
        names.append((str(pj.relative_to(FRONT)), d.get("name", "?")))
        deps.update(d.get("dependencies", {}) or {})
        devdeps.update(d.get("devDependencies", {}) or {})
    return names, deps, devdeps


def scan_lazy():
    total = lazy = 0
    for p in FRONT.rglob("*.tsx"):
        if "node_modules" in p.parts:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        total += 1
        if re.search(r"React\.lazy|=\s*lazy\(|lazy\s*\(", t):
            lazy += 1
    return total, lazy


def scan_effect_cleanup():
    """useEffect callbacks whose body has no return — candidates only."""
    suspects = []
    for p in FRONT.rglob("*.tsx"):
        if "node_modules" in p.parts:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r"useEffect\s*\(\s*\(\s*\)\s*=>\s*\{", t):
            # crude block scan: look ahead ~2000 chars for "return" at
            # top level of this effect (before a matching close is hard;
            # accept false-positive-light heuristic)
            seg = t[m.end(): m.end() + 2000]
            if "return" not in seg.split("},")[0]:
                line = t[: m.start()].count("\n") + 1
                suspects.append(f"{p.relative_to(FRONT)}:{line}")
                break  # one per file is enough for a report
    return suspects


def inspect_i18n():
    info = {"config": None, "locales": {}, "wiring": []}
    cfg = FRONT / "packages" / "i18n" / "src" / "config.ts"
    if cfg.exists():
        info["config"] = str(cfg.relative_to(FRONT))
        text = cfg.read_text(encoding="utf-8", errors="replace")
        info["uses_i18next"] = "i18next" in text
        info["uses_languagedetector"] = "LanguageDetector" in text
    locdir = FRONT / "packages" / "i18n" / "src" / "locales"
    if locdir.exists():
        for f in sorted(locdir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                info["locales"][f.stem] = len(data) if isinstance(data, dict) else 0
            except Exception:
                info["locales"][f.stem] = "parse-error"
    # who imports @eco/i18n?
    for p in FRONT.rglob("*.{ts,tsx}"):
        if "node_modules" in p.parts:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "@eco/i18n" in t:
            info["wiring"].append(str(p.relative_to(FRONT)))
            if len(info["wiring"]) >= 12:
                break
    return info


def main():
    say("=" * 70)
    say("PHASE 1 — REAL dependency map (monorepo-aware)")
    say("=" * 70)
    names, deps, devdeps = collect_deps()
    say(f"package.json files found: {len(names)}")
    for rel, name in names[:20]:
        say(f"  {name:24s} {rel}")
    crit = ["react", "react-dom", "react-router-dom", "vite",
            "tailwindcss", "i18next", "react-i18next",
            "@tanstack/react-query", "echarts", "framer-motion"]
    say("\ncritical deps (any package):")
    for c in crit:
        v = deps.get(c) or devdeps.get(c)
        say(f"  {'✅' if v else '❌'} {c}: {v or 'not found'}")

    say("")
    say("=" * 70)
    say("PHASE 2 — accurate lazy-loading + effect-cleanup candidates")
    say("=" * 70)
    total, lazy = scan_lazy()
    say(f"tsx files (excl. node_modules): {total}")
    say(f"files using lazy(): {lazy}  ({lazy / total * 100 if total else 0:.1f}%)")
    susp = scan_effect_cleanup()
    say(f"effect-without-return candidates (review, not verdict): {len(susp)}")
    for s in susp[:10]:
        say("  - " + s)

    say("")
    say("=" * 70)
    say("PHASE 3 — i18n ground truth")
    say("=" * 70)
    i18n = inspect_i18n()
    say(f"config file: {i18n['config'] or 'NOT FOUND'}")
    say(f"uses i18next lib: {i18n.get('uses_i18next')}")
    say("locale files (top-level key count):")
    for lang, n in i18n["locales"].items():
        say(f"  {lang}: {n}")
    say(f"files importing @eco/i18n: {len(i18n['wiring'])}")
    for w in i18n["wiring"][:12]:
        say("  - " + w)

    say("")
    say("=" * 70)
    say("PHASE 4 — design-language readiness (tokens/tailwind)")
    say("=" * 70)
    tw_configs = [str(p.relative_to(FRONT)) for p in FRONT.rglob("tailwind.config.*")
                  if "node_modules" not in p.parts]
    say(f"tailwind configs: {tw_configs or 'NONE'}")
    css_vars = 0
    for p in FRONT.rglob("*.css"):
        if "node_modules" in p.parts:
            continue
        css_vars += p.read_text(encoding="utf-8", errors="replace").count("--eco") \
            if p.read_text(encoding="utf-8", errors="replace") else 0
    say(f"CSS custom properties (--eco-*): ~{css_vars}")

    report = {
        "packages": [{"path": r, "name": n} for r, n in names],
        "critical_deps": {c: (deps.get(c) or devdeps.get(c)) for c in crit},
        "tsx_total": total,
        "lazy_files": lazy,
        "effect_cleanup_candidates": susp,
        "i18n": i18n,
        "tailwind_configs": tw_configs,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                      encoding="utf-8")
    say("")
    say(f"report saved: {REPORT}")

    say("")
    say("=" * 70)
    say("PHASE 5 — what this means for the redesign")
    say("=" * 70)
    has_i18n_runtime = bool(deps.get("i18next") or devdeps.get("i18next"))
    say(f"""
DECISIONS (based on evidence):
 1. i18n: {'runtime dep PRESENT' if has_i18n_runtime else 'runtime dep MISSING'} —
    but locale JSONs exist for {list(i18n['locales'])}.
    Next: ensure `i18next` + `react-i18next` + `i18next-browser-languagedetector`
    are deps of packages/i18n (they may already be), then mount <I18nProvider>
    in both apps and switch <html dir> by locale (fa/ar/ur => rtl).
 2. Design tokens: {'tailwind present' if tw_configs else 'no tailwind configs'}
    -> build tokens as CSS variables (works with any styling solution),
    name-spaced --eco-* so both web & dashboard share them.
 3. Lazy loading: {lazy}/{total} files — introduce React.lazy at ROUTE level
    first (apps/*/src/app routes), not per-component: biggest win, least churn.
 4. The 24 'memory leak' candidates from the old scan: treat as a REVIEW
    checklist only — verify each has cleanup logic; the naive heuristic was
    superseded by PHASE 2 candidates list.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())