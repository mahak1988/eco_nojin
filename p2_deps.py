# -*- coding: utf-8 -*-
"""
p2_deps.py — ممیزی وابستگی‌های فرانت‌اند (فاز P2 — گام ۱)
اسکن واقعی import ها در src + کانفیگ‌ها و مقایسه با package.json
خروجی: گزارش کنسول + P2_DEPS_REPORT.md + دستورات آماده pnpm
اجرا:
    python p2_deps.py           # فقط گزارش (بی‌خطر)
    python p2_deps.py --apply   # حذف خودکار موارد قطعی + راستی‌آزمایی build/test
"""
import json, re, subprocess, sys
from pathlib import Path
from collections import defaultdict

FE = (Path(__file__).resolve().parent / "frontend").resolve()
SRC = FE / "src"

PATTERNS = [
    re.compile(r"""\bfrom\s+["']([^"']+)["']"""),
    re.compile(r"""(?:^|[^\w.])import\s+["']([^"']+)["']"""),
    re.compile(r"""\bimport\s*\(\s*["']([^"']+)["']"""),
    re.compile(r"""\brequire\s*\(\s*["']([^"']+)["']"""),
    re.compile(r"""@import\s+["']([^"']+)["']"""),
]

def bare_name(spec: str):
    if not spec or spec.startswith((".", "/")): return None
    if spec.startswith("@/"): return None            # alias داخلی پروژه
    if spec.startswith("@"):
        parts = spec.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else None
    return spec.split("/")[0]

WHITELIST = {  # ابزارهای build/تست که با import مستقیم مصرف نمی‌شوند
    "vite", "typescript", "vitest", "jsdom", "eslint", "globals",
    "@eslint/js", "eslint-plugin-react-hooks", "eslint-plugin-react-refresh",
    "typescript-eslint", "@vitejs/plugin-react",
}

SUSPECT = {
    "terraformer": "🪦 منسوخ (Esri آرشیو کرده) — جایگزین: @terraformer/arcgis یا turf",
    "georaster-layer-for-leaflet": "⚠️ به leaflet نیاز دارد که در dependencies نیست!",
    "@types/mapbox-gl": "🪦 stub منسوخ — خود mapbox-gl اصلاً نصب نیست",
    "@types/maplibre-gl": "🪦 stub منسوخ — maplibre-gl تایپ داخلی دارد",
    "@web3modal/wagmi": "🔁 منسوخ → Reown AppKit (مهاجرت در نسخه بعدی)",
}

def find_pnpm():
    for c in ("pnpm", str(Path.home() / "AppData/Local/pnpm/pnpm.EXE")):
        try:
            if subprocess.run([c, "--version"], capture_output=True, timeout=15).returncode == 0:
                return c
        except Exception:
            continue

def scan_imports():
    used = defaultdict(set)
    targets = [p for p in SRC.rglob("*")
               if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".css"}]
    targets += list(FE.glob("*.ts")) + list(FE.glob("*.js"))  # کانفیگ‌های ریشه frontend
    for f in targets:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in PATTERNS:
            for m in pat.finditer(text):
                b = bare_name(m.group(1))
                if b:
                    used[b].add(f.relative_to(FE).as_posix())
    return used

def main():
    apply_mode = "--apply" in sys.argv
    print("═" * 58 + "\n📦 p2_deps.py — ممیزی وابستگی‌های فرانت‌اند\n" + "═" * 58)
    data = json.loads((FE / "package.json").read_text(encoding="utf-8"))
    deps, dev = data.get("dependencies", {}), data.get("devDependencies", {})
    all_declared = {**deps, **dev}
    used = scan_imports()

    unused_runtime = sorted(d for d in deps if d not in used and d not in WHITELIST)
    unused_dev     = sorted(d for d in dev if d not in used and d not in WHITELIST
                            and not d.startswith("@types/"))
    unused_types   = [d for d in dev if d.startswith("@types/") and d not in used]
    orphan_types   = sorted(t for t in unused_types if t[7:] not in all_declared)
    ghosts         = sorted(b for b in used if b not in all_declared)

    rep, A = [], (lambda s: rep.append(s))
    A("# 📦 گزارش ممیزی وابستگی‌های فرانت‌اند\n")

    A("## ۱) runtime-dep های بلااستفاده (کاندید حذف)\n")
    if unused_runtime:
        for d in unused_runtime:
            A(f"- `{d}` {deps[d]} — مصرف در کد: صفر" +
              (f" — {SUSPECT[d]}" if d in SUSPECT else ""))
        A(f"\n**دستور:** `pnpm remove {' '.join(unused_runtime)}`")
    else:
        A("- هیچ ✅")
    A("")

    A("## ۲) @types یتیم (پکیج اصلی‌اش اصلاً نصب نیست)\n")
    A("\n".join(f"- `{t}`" for t in orphan_types) or "- هیچ ✅")
    if orphan_types:
        A(f"\n**دستور:** `pnpm remove {' '.join(orphan_types)}`")
    A("")

    A("## ۳) dev-dep های بلااستفاده (بازبینی دستی)\n")
    A("\n".join(f"- `{d}`" for d in unused_dev) or "- هیچ ✅")
    A("")

    A("## ۴) import شده ولی اعلان‌نشده (ghost)\n")
    if ghosts:
        for g in ghosts:
            A(f"- `{g}` ← در {len(used[g])} فایل")
        A(f"\n**دستور:** `pnpm add {' '.join(ghosts)}`")
    else:
        A("- هیچ ✅")
    A("")

    A("## ۵) هشدارهای نگهداری\n")
    notes = [f"- {SUSPECT[d]}" for d in all_declared if d in SUSPECT]
    if "georaster-layer-for-leaflet" in used and "leaflet" not in all_declared:
        notes.append("- 🚨 کد به georaster-layer-for-leaflet ارجاع دارد ولی `leaflet` "
                     "نصب نیست → crash در زمان اجرا!")
    A("\n".join(notes) or "- هیچ ✅")
    A("")

    A("## ۶) پرکاربردترین‌ها (۱۰ مورد اول)\n")
    top = sorted(used.items(), key=lambda kv: -len(kv[1]))[:10]
    A("\n".join(f"- `{k}` — {len(v)} فایل" for k, v in top))

    (FE.parent / "P2_DEPS_REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep))
    print("📄 ذخیره شد: P2_DEPS_REPORT.md")

    # ---------- حذف خودکار (فقط موارد قطعی + راستی‌آزمایی) ----------
    to_remove = unused_runtime + orphan_types
    if not to_remove:
        print("\n✅ چیزی برای حذف نیست — وابستگی‌ها تمیزند")
        return
    if not apply_mode:
        print(f"\n💡 حذف خودکار {len(to_remove)} مورد:  python p2_deps.py --apply")
        return
    pnpm = find_pnpm()
    if pnpm is None:
        print(f"❌ pnpm پیدا نشد — دستی: pnpm remove {' '.join(to_remove)}")
        return
    if input(f"\n⚠️ حذف {len(to_remove)} پکیج + build/test راستی‌آزمایی؟ (y/N): ").lower() != "y":
        print("↷ رد شد"); return
    if subprocess.run([pnpm, "remove"] + to_remove, cwd=str(FE)).returncode != 0:
        print("❌ pnpm remove ناموفق"); return
    print("✅ حذف شد — راستی‌آزمایی...")
    for cmd in ([pnpm, "run", "build"], [pnpm, "test"]):
        if subprocess.run(cmd, cwd=str(FE)).returncode != 0:
            print(f"⚠️ «{cmd[-1]}» شکست خورد — بازگرداندن:\n"
                  "   git checkout frontend/package.json frontend/pnpm-lock.yaml ; pnpm install")
            return
    print("🎉 حذف بدون شکستگی تأیید شد — کامیت کنید:")
    print('   git add -A ; git commit -m "chore(deps): remove unused frontend dependencies"')

if __name__ == "__main__":
    main()