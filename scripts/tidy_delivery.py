"""مرتب‌سازی پوشهٔ تحویل — پوشهٔ «کتابها».

قاعده: **در ریشه فقط سند تحویل می‌ماند.** هر چیز دیگر — پشتیبان تاریخ‌دار،
نسخهٔ میانی، فایل بازیابی، خروجی ابزار — به `_منتقل-شده` می‌رود.

سند تحویل آن است که:
  - پسوند `.txt` یا `.md` دارد
  - نامش به `.bak` ختم نمی‌شود
  - نامش یک الگوی تاریخ‌دار ندارد: `<چیزی>.<YYYYMMDD-HHMM>.<فاز>.bak`
  - نامش یک الگوی بازیابی ندارد: `...pre-voice` · `...pre-struct` ·
    `...pre-census` · `...pre-nutrient-section` · `...pre-voice.bak` ·
    `...pre-floor` · `...pre-block13` · `...pre-repair` · `...pre-integr` ·
    `...cleanup-baseline` · `...pre-complete` · `...pre-deadend` ·
    `...pre-deadend-zero` · `...pre-expand` · `...pre-booklet` ·
    `...pre-structure` · `...pre-struct13b` · `...v3.1-complete`

اجرا:
  python scripts/tidy_delivery.py          # فقط گزارش
  python scripts/tidy_delivery.py --apply  # اجرا
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "کتابها")
HOLD = os.path.join(BOOKS, "_منتقل-شده")

STAMPED = re.compile(r"\.\d{8}-\d{4}\.")
INTERMEDIATE = (
    "pre-voice",
    "pre-struct",
    "pre-census",
    "pre-nutrient-section",
    "pre-floor",
    "pre-block13",
    "pre-repair",
    "pre-integr",
    "pre-integration",
    "cleanup-baseline",
    "pre-complete",
    "pre-deadend",
    "pre-deadend-zero",
    "pre-expand",
    "pre-booklet",
    "pre-structure",
    "pre-struct13b",
    "pre-carbon-reprice",
    "pre-booklet",
    "pre-source",
    "pre-template",
    "pre-struct-blocks",
    "v3.1-complete",
)
DELIVERY_SUFFIX = (".txt", ".md")
MERGE_FOLDERS = ("_archive", "_پشتیبان", "_bak", "_backup")


def is_delivery(name: str) -> bool:
    if not name.lower().endswith(DELIVERY_SUFFIX):
        return False
    if name.startswith("_"):
        return False
    if STAMPED.search(name):
        return False
    return not any(marker in name for marker in INTERMEDIATE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not os.path.isdir(BOOKS):
        print(f"پوشه یافت نشد: {BOOKS}", file=sys.stderr)
        return 2

    delivery, strays, folders = [], [], []
    for name in sorted(os.listdir(BOOKS)):
        path = os.path.join(BOOKS, name)
        if os.path.isdir(path):
            folders.append(name)
            continue
        (delivery if is_delivery(name) else strays).append(name)

    print(
        f"ریشه: {len(delivery)} سند تحویل · {len(folders)} پوشه · {len(strays)} فایل ناگزیر به انتقال"
    )
    if not strays and not [f for f in folders if f in MERGE_FOLDERS]:
        print("نیازی به جابه‌جایی نیست")
        return 0

    if strays:
        print("\nسند تحویل:")
        for name in delivery:
            print(f"  · {name}")
        print("\nانتقال می‌شود:")
        for name in strays:
            print(f"  · {name}")

    if not args.apply:
        print("\nبرای اجرا: python scripts/tidy_delivery.py --apply")
        return 0

    os.makedirs(HOLD, exist_ok=True)
    moved = 0
    for name in strays:
        source = os.path.join(BOOKS, name)
        target = os.path.join(HOLD, name)
        if os.path.exists(target):
            base, ext = os.path.splitext(name)
            index = 1
            while os.path.exists(os.path.join(HOLD, f"{base}__تکراری{index}{ext}")):
                index += 1
            target = os.path.join(HOLD, f"{base}__تکراری{index}{ext}")
        shutil.move(source, target)
        moved += 1

    for name in list(os.listdir(BOOKS)):
        if name in MERGE_FOLDERS:
            folder = os.path.join(BOOKS, name)
            for entry in os.listdir(folder):
                source = os.path.join(folder, entry)
                if not os.path.isfile(source):
                    continue
                target = os.path.join(HOLD, entry)
                if os.path.exists(target):
                    base, ext = os.path.splitext(entry)
                    index = 1
                    while os.path.exists(os.path.join(HOLD, f"{base}__تکراری{index}{ext}")):
                        index += 1
                    target = os.path.join(HOLD, f"{base}__تکراری{index}{ext}")
                shutil.move(source, target)
                moved += 1
            shutil.rmtree(folder)

    print(f"\nمنتقل‌شده: {moved} فایل به _منتقل-شده")
    print(
        f"باقی‌مانده در ریشه: {len([f for f in os.listdir(BOOKS) if os.path.isfile(os.path.join(BOOKS, f))])} سند"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
