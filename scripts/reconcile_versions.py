"""یکسان‌سازی کنترل نسخه — بند ۱۲٫۱ استاندارد نگارش.

هفت سند تعارض نسخه دارند: سربرگ، کد سند، سطر پایان و تاریخچه چهار عدد
متفاوت نشان می‌دهند. قاعدهٔ حاکم: **تاریخچه رکورد است و سربرگ ادعا.**

این ابزار هرگز نسخه را پایین نمی‌آورد. بالاترین شماره‌ای که هرجا ادعا شده
مبنا قرار می‌گیرد، یک سطح بالا می‌رود، و یک ردیف تاریخچه اضافه می‌شود که
همان یکسان‌سازی و اصلاحات پس از آخرین ردیف قبلی را نام می‌برد.

اجرا:  python scripts/reconcile_versions.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "کتابها")
DATE = "۱۴۰۵/۰۶/۲۸"
VER = re.compile(r"v(\d+)\.(\d+)")

NOTE = (
    "یکسان‌سازی کنترل نسخه — سربرگ، کد سند، سطر پایان و تاریخچه یکسان شدند · "
    "اصلاح شمار جدول‌ها و شکل‌ها با شمارش ماشینی و اعلام قاعدهٔ شمارش · "
    "حذف سطرهای تکراری و ادغام جدول‌های هم‌شماره · "
    "افزودن بلوک «سند اصلی این بسته»، جدول نگاشت افعال وجهی و خلاصهٔ عدم‌قطعیت هر فصل · "
    "صفر بن‌بست و صفر نقض بند ۷"
)


def versions_in(text: str) -> set[tuple[int, int]]:
    return {(int(a), int(b)) for a, b in VER.findall(text)}


def bump(pairs: set[tuple[int, int]]) -> tuple[int, int]:
    major, minor = max(pairs)
    return (major, minor + 1)


def fmt(p: tuple[int, int]) -> str:
    return f"v{p[0]}.{p[1]}"


def reconcile(name: str, apply: bool) -> dict | None:
    path = os.path.join(BOOKS, name)
    if not os.path.isfile(path):
        return None
    raw = open(path, encoding="utf-8", newline="").read()
    lines = raw.split("\n")
    found = versions_in(raw)
    if not found:
        return None

    header = next((re.search(r"v(\d+)\.(\d+)", l) for l in lines[:30] if "نسخه" in l and re.search(r"v\d+\.\d+", l)), None)
    code = next((re.search(r"ENG-v(\d+)\.(\d+)", l) for l in lines[:30] if "ENG-v" in l), None)
    hist = [re.match(r"^v(\d+)\.(\d+)\t", l) for l in lines]
    hist = [h for h in hist if h]
    last = next((re.search(r"v(\d+)\.(\d+)", l) for l in reversed(lines) if "پایان" in l and VER.search(l)), None)

    seen = {tuple(map(int, m.groups())) for m in (header, code, last)} if (header and code and last) else set()
    latest_hist = tuple(map(int, hist[-1].groups())) if hist else None
    allvals = seen | ({latest_hist} if latest_hist else set())
    if len(allvals) < 2:
        return None

    new = bump(found)
    old = fmt(max(found))
    plan = {"file": name, "from": old, "to": fmt(new), "changes": []}

    if apply:
        text = raw
        # تاریخچه: ردیف تازه درست پس از آخرین ردیف
        if hist:
            idx = max(i for i, l in enumerate(lines) if re.match(r"^v\d+\.\d+\t", l))
            row = f"{fmt(new)}\t{DATE}\t{NOTE}"
            lines.insert(idx + 1, row)
            plan["changes"].append("ردیف تاریخچه افزوده شد")
        # سربرگ
        for i, l in enumerate(lines):
            if i < 30 and "نسخه" in l and VER.search(l) and "کد سند" not in l:
                lines[i] = re.sub(r"v\d+\.\d+", fmt(new), l, count=1)
                plan["changes"].append(f"سربرگ سطر {i+1}")
                break
        # کد سند
        for i, l in enumerate(lines):
            if i < 30 and "ENG-v" in l:
                lines[i] = re.sub(r"ENG-v\d+\.\d+", f"ENG-{fmt(new)}", l, count=1)
                plan["changes"].append(f"کد سند سطر {i+1}")
                break
        # سطر پایان
        for i in range(len(lines) - 1, -1, -1):
            if "پایان" in lines[i] and VER.search(lines[i]):
                lines[i] = re.sub(r"v\d+\.\d+", fmt(new), lines[i])
                lines[i] = re.sub(r"ENG-v\d+\.\d+", f"ENG-{fmt(new)}", lines[i])
                plan["changes"].append("سطر پایان")
                break
        io.open(path, "w", encoding="utf-8", newline="").write("\n".join(lines))

    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    plans = []
    for name in sorted(os.listdir(BOOKS)):
        if not name.endswith((".txt", ".md")) or name.startswith("_") or ".bak" in name:
            continue
        plan = reconcile(name, args.apply)
        if plan:
            plans.append(plan)

    if not plans:
        print("تعارض نسخه یافت نشد")
        return 0
    for p in plans:
        action = " · ".join(p["changes"]) if args.apply else "بدون اعمال"
        print(f"  {p['file'][:36]:<38} {p['from']} ← {p['to']}   {action}")
    if not args.apply:
        print("\nبرای اجرا: python scripts/reconcile_versions.py --apply")
    else:
        print(f"\nیکسان‌سازی‌شده: {len(plans)} سند")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
