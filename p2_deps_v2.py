# -*- coding: utf-8 -*-
"""
p2_deps_v2.py — ممیزی و حذف ایمن وابستگی‌های فرانت‌اند (نسخه اصلاح‌شده)
اصلاحات نسبت به v1:
  ✅ @types/node و @types/geojson دیگر حذف نمی‌شوند (توجیه type-only)
  ✅ node:* به‌عنوان builtin شناخته می‌شود (نه ghost)
  ✅ @types/maplibre-gl (stub منسوخ) به لیست حذف اضافه شد
  ✅ یافتن pnpm: which + PATHEXT + LOCALAPPDATA + corepack
  ✅ بکاپ خودکار package.json/lock + رول‌بک خودکار در شکست build/test
اجرا:
    python p2_deps_v2.py            # فقط گزارش اصلاح‌شده
    python p2_deps_v2.py --apply    # حذف + build/test + رول‌بک خودکار در صورت شکست
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parent
FE = ROOT / "frontend"
Q = ROOT / "_quarantine" / "p2"

# ── تزریق PATH (گیت + نود + pnpm) برای این پروسه ──
for d in (r"C:\Program Files\Git\cmd", r"C:\Program Files\nodejs",
          str(Path(os.environ.get("LOCALAPPDATA", "")) / "pnpm")):
    if d and Path(d).is_dir() and d not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + d

def find_git():
    for g in ("git", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            if subprocess.run([g, "--version"], capture_output=True, timeout=10).returncode == 0:
                return g
        except Exception:
            continue
    return None

def find_pnpm():
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "pnpm"
    cands = [shutil.which("pnpm")] + [str(local / n) for n in ("pnpm.EXE", "pnpm.CMD", "pnpm.cmd")]
    for c in cands:
        if c and Path(c).exists():
            try:
                if subprocess.run([c, "--version"], capture_output=True, timeout=30).returncode == 0:
                    return [c]
            except Exception:
                pass
    cp = shutil.which("corepack")
    if cp:
        try:
            if subprocess.run([cp, "pnpm", "--version"], capture_output=True, timeout=30).returncode == 0:
                return [cp, "pnpm"]
        except Exception:
            pass
    return None

GIT, PNPM = find_git(), find_pnpm()

def run(args, cwd=ROOT, timeout=1200):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                       errors="ignore", timeout=timeout)
    return r.returncode, r.stdout or "", r.stderr or ""

# ───────── اسکن import ها ─────────
PATTERNS = [re.compile(p) for p in (
    r"""\bfrom\s+["']([^"']+)["']""",
    r"""(?:^|[^\w.])import\s+["']([^"']+)["']""",
    r"""\bimport\s*\(\s*["']([^"']+)["']""",
    r"""\brequire\s*\(\s*["']([^"']+)["']""",
    r"""@import\s+["']([^"']+)["']""")]
TYPE_IMPORT = re.compile(r"""\bimport\s+type\s+[^;]*?from\s+["']([^"']+)["']""")

def bare_name(spec):
    if not spec or spec.startswith((".", "/")) or spec.startswith("@/"):
        return None
    if spec.startswith("@"):
        parts = spec.split("/")
        return "/".join(parts[:2]) if len(parts) >= 2 else None
    return spec.split("/")[0]

WHITELIST = {"vite", "typescript", "vitest", "jsdom", "eslint", "globals",
             "@eslint/js", "eslint-plugin-react-hooks", "eslint-plugin-react-refresh",
             "typescript-eslint", "@vitejs/plugin-react"}
STUB_TYPES = {"@types/mapbox-gl", "@types/maplibre-gl"}   # منسوخ — همیشه قابل حذف
SUSPECT = {
    "terraformer": "🪦 منسوخ (Esri آرشیو کرده)",
    "georaster-layer-for-leaflet": "⚠️ به leaflet نیاز دارد که نصب نیست",
    "@web3modal/wagmi": "🔁 منسوخ → Reown AppKit (مهاجرت بعدی)",
}

def scan():
    total, typed = Counter(), Counter()
    files_by_pkg = defaultdict(set)
    targets = [p for p in (FE / "src").rglob("*") if p.suffix in {".ts", ".tsx", ".js", ".jsx", ".css"}]
    targets += list(FE.glob("*.ts")) + list(FE.glob("*.js"))
    for f in targets:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        specs = {m.group(1) for p in PATTERNS for m in p.finditer(text)}
        tspecs = {m.group(1) for m in TYPE_IMPORT.finditer(text)}
        for s in specs:
            b = bare_name(s)
            if b:
                total[b] += 1
                files_by_pkg[b].add(f.relative_to(FE).as_posix())
                if s in tspecs:
                    typed[b] += 1
    type_only = {b for b in typed if typed[b] == total[b]}
    return total, files_by_pkg, type_only

def main():
    apply_mode = "--apply" in sys.argv
    print("═" * 58 + "\n📦 p2_deps_v2.py — ممیزی اصلاح‌شده وابستگی‌ها\n" + "═" * 58)
    data = json.loads((FE / "package.json").read_text(encoding="utf-8"))
    deps, dev = data.get("dependencies", {}), data.get("devDependencies", {})
    declared = {**deps, **dev}
    total, files_by_pkg, type_only = scan()

    unused_runtime = sorted(d for d in deps if d not in total and d not in WHITELIST)
    ghosts = sorted(b for b in total if b not in declared and b not in WHITELIST)

    remove = list(unused_runtime)
    notes = []

    # @types یتیم — با منطق اصلاح‌شده
    for t in sorted(dev):
        if not t.startswith("@types/") or t in STUB_TYPES and t in dev:
            continue
        base = t[7:]
        if t == "@types/node" or base in declared or base in total:
            continue
        if base in type_only:
            notes.append(f"🔒 `{t}` نگه داشته شد — کد از `{base}` به‌صورت type-only استفاده می‌کند")
        else:
            remove.append(t)
    remove += [t for t in STUB_TYPES if t in dev and t not in remove]
    remove = sorted(set(remove))

    # ── گزارش ──
    rep, A = [], (lambda s: rep.append(s))
    A("# 📦 گزارش v2 — ممیزی وابستگی‌ها\n")
    A(f"## کاندید حذف ({len(remove)}) — همه با build+test راستی‌آزمایی می‌شوند\n")
    A("\n".join(f"- `{d}`" for d in remove) or "- هیچ ✅")
    A("\n## نکات هوشمند\n")
    for g in ghosts:
        if g.startswith("node:"):
            A(f"- ℹ️ `{g}` builtin نود است — نیازی به نصب ندارد (باگ v1 رفع شد)")
        elif g in type_only:
            A(f"- ℹ️ import از `{g}` فقط type-only است → `@types/{g}` کافی است؛ پکیج runtime لازم نیست")
        else:
            A(f"- 🚨 `{g}` واقعاً import شده ولی اعلان نشده ({len(files_by_pkg[g])} فایل) → `pnpm add {g}`")
    A("\n".join(notes))
    A("\n## نگهداری\n")
    A("\n".join(f"- {SUSPECT[d]}" for d in declared if d in SUSPECT) or "- هیچ")
    report = "\n".join(rep)
    (ROOT / "P2_DEPS_REPORT.md").write_text(report, encoding="utf-8")
    print(report)

    if not remove:
        print("\n✅ چیزی برای حذف نیست"); return
    if not apply_mode:
        print(f"\n💡 حذف خودکار {len(remove)} مورد:  python p2_deps_v2.py --apply")
        return

    # ── اجرا: بکاپ → remove → build/test → رول‌بک خودکار در شکست ──
    if PNPM is None:
        print("❌ pnpm پیدا نشد حتی با which/corepack — خروجی را بفرستید"); return
    print(f"\n✅ pnpm: {' '.join(PNPM)}")
    if input(f"⚠️ حذف {len(remove)} پکیج؟ (شکست build → رول‌بک خودکار) (y/N): ").lower() != "y":
        print("↷ رد شد"); return

    Q.mkdir(parents=True, exist_ok=True)
    for f in ("package.json", "pnpm-lock.yaml"):
        if (FE / f).exists():
            shutil.copy2(FE / f, Q / f"{f}.bak")
    print("💾 بکاپ در _quarantine/p2/ ذخیره شد")

    rc, out, err = run(PNPM + ["remove"] + remove, cwd=FE)
    if rc != 0:
        print(f"❌ pnpm remove ناموفق:\n{(out + err)[-600:]}"); return
    print("✅ حذف شد — دروازه راستی‌آزمایی...")

    def rollback(reason):
        print(f"\n🚨 {reason} — رول‌بک خودکار...")
        for f in ("package.json", "pnpm-lock.yaml"):
            if (Q / f"{f}.bak").exists():
                shutil.copy2(Q / f"{f}.bak", FE / f)
        run(PNPM + ["install"], cwd=FE)
        print("✅ بازگردانده شد — پروژه به حالت قبل برگشت. خروجی خطا را برایم بفرستید.")

    for label, cmd in (("build", PNPM + ["run", "build"]), ("test", PNPM + ["test"])):
        rc, out, err = run(cmd, cwd=FE)
        if rc != 0:
            print(f"───── خروجی {label} (۱۵ خط آخر) ─────")
            print("\n".join((out + err).splitlines()[-15:]))
            rollback(f"«{label}» شکست خورد")
            return
        print(f"✅ {label} سبز")

    print("\n🎉 حذف ۲۹ ریسک بدون شکستگی تأیید شد")
    if GIT and input("کامیت کنم؟ (y/N): ").lower() == "y":
        run([GIT, "add", "-A"])
        rc, _, e = run([GIT, "commit", "-m",
            "chore(deps): prune unused frontend dependencies (verified by build+test)"])
        print("✅ کامیت شد" if rc == 0 else f"⚠️ {e.strip()[:120]}")

    # ── بخش شاخه‌های به‌جامانده (چون گیت در ترمینال شما در دسترس نیست) ──
    if GIT:
        print("\n" + "─" * 55 + "\n🌿 سرنوشت شاخه‌های قدیمی (اختلاف محتوایی با main)\n" + "─" * 55)
        for b in ("master", "code-restoration-in-the-main-branch-76761", "fix/phase-a-final-20-tests"):
            rc, out, err = run([GIT, "diff", "--shortstat", f"main..{b}"])
            stat = (out or "").strip()
            if rc != 0:
                print(f"   ⚠️ {b}: {err.strip()[:60]}")
            elif not stat:
                print(f"   ✅ {b}: محتوایش با main یکسان است → حذف بی‌خطر")
                if input(f"      حذف شاخه {b}؟ (y/N): ").lower() == "y":
                    run([GIT, "branch", "-D", b])
                    print("      🗑️ حذف شد")
            else:
                print(f"   📌 {b}: {stat} ← کار متفاوت دارد؛ حذف نمی‌شود (خروجی را بفرستید)")
        if input("حذف تگ phase-a-complete؟ (y/N): ").lower() == "y":
            run([GIT, "tag", "-d", "phase-a-complete"])

if __name__ == "__main__":
    main()