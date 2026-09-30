"""موج صفر — ساخت رجیستر یکپارچهٔ پیش‌نویس و تخصیص شناسه به هر بسته.

دو مجموعهٔ کاندید را ادغام می‌کند:
  scripts/hdr_candidates.csv        از پیوست الف
  scripts/hdr_body_candidates.csv   از بدنهٔ فصل‌ها

سپس نویز را پاک می‌کند، شناسهٔ یکتا می‌سازد، ردیف‌های تکراری با رجیستر
موجود را کنار می‌گذارد، و برای هر بسته یک فهرست شناسهٔ تخصیص‌یافته می‌نویسد
تا نویسندهٔ هر کتابچه بداند باید به چه شناسه‌هایی ارجاع دهد.

خروجی:
  scripts/HDR_draft.csv        رجیستر پیش‌نویس یکپارچه
  scripts/hdr_assignments.md   شناسه‌های تخصیص‌یافته به تفکیک بسته

اجرا:  python scripts/merge_hdr_draft.py
"""

from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOOKS = os.path.join(ROOT, "کتابها")
REGISTER = os.path.join(BOOKS, "_مرجع", "HDR.csv")
SRC_A = os.path.join(HERE, "hdr_candidates.csv")
SRC_B = os.path.join(HERE, "hdr_body_candidates.csv")
OUT_CSV = os.path.join(HERE, "HDR_draft.csv")
OUT_MD = os.path.join(HERE, "hdr_assignments.md")

FIELDS = [
    "id",
    "domain",
    "indicator",
    "value",
    "unit",
    "source_primary",
    "year",
    "confidence",
    "consumers",
    "action",
    "status",
]

# سطرهایی که تاریخ یا شناسهٔ موجود رجیستر هستند و رکورد تازه نیستند
ALREADY = re.compile(r"شروع رسمی طرح|بازهٔ زمانی|نرخ ارز مرجع|تعداد (شکل|جدول|فرمول|ردیف)")
FRAGMENT = re.compile(r"^[^:]{0,30}$")


def noise(label: str, value: str) -> str | None:
    """دلیل حذف یک ردیف، یا None اگر سالم باشد."""
    if ALREADY.search(label):
        return "تکرار ردیف ثابت رجیستر"
    if not re.search(r"[۰-۹0-9]", value):
        return "مقدار بدون رقم"
    if len(label) < 6:
        return "برچسب بیش از حد کوتاه"
    if FRAGMENT.match(label) and " " not in label.strip():
        return "برچسب تک‌واژه‌ای"
    if re.search(r"[آ-ی]{2,}\s*»\s*است", label):
        return "قطعهٔ جمله"
    return None


def main() -> int:
    for path in (REGISTER, SRC_A, SRC_B):
        if not os.path.exists(path):
            print(f"فایل یافت نشد: {path}", file=sys.stderr)
            return 2

    with open(REGISTER, encoding="utf-8") as handle:
        existing = {r["id"].strip() for r in csv.DictReader(handle)}
    with open(REGISTER, encoding="utf-8") as _fh:
        existing_indicators = {r["indicator"].strip() for r in csv.DictReader(_fh)}

    merged: list[dict] = []
    for src in (SRC_A, SRC_B):
        with open(src, encoding="utf-8") as handle:
            merged.extend(csv.DictReader(handle))

    kept: list[dict] = []
    dropped: Counter[str] = Counter()
    for row in merged:
        reason = noise(row["indicator"], row["value"])
        if reason:
            dropped[reason] += 1
            continue
        if row["indicator"].strip() in existing_indicators:
            dropped["شاخص تکراری با رجیستر موجود"] += 1
            continue
        kept.append(row)

    # شاخص یکتا در کل مجموعه
    spread: dict[str, set[str]] = defaultdict(set)
    for row in kept:
        spread[row["indicator"]].add(row["consumers"])
    for row in kept:
        if len(spread[row["indicator"]]) > 1:
            row["indicator"] = f"{row['indicator']} — {row['consumers']}"

    # شناسهٔ یکتا، با پرهیز از شناسه‌های موجود
    counters: dict[str, int] = defaultdict(int)
    used: set[str] = set()
    for row in kept:
        family = re.match(r"^[A-Z]+", row["id"])
        family = family.group(0) if family else "TO"
        # اگر شناسهٔ قبلی خانواده را نداشته، از ستون id کاندید استفاده کن
        while True:
            counters[family] += 1
            new_id = f"{family}-{counters[family]:02d}"
            if new_id not in existing and new_id not in used:
                break
        row["id"] = new_id
        used.add(new_id)

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in kept:
            writer.writerow({k: row.get(k, "") for k in FIELDS})

    by_book: dict[str, list[dict]] = defaultdict(list)
    for row in kept:
        by_book[row["consumers"]].append(row)

    with open(OUT_MD, "w", encoding="utf-8") as handle:
        handle.write("# شناسه‌های تخصیص‌یافتهٔ رجیستر — به تفکیک بسته\n\n")
        handle.write(f"ردیف‌های نگه‌داشته‌شده: **{len(kept)}** · حذف‌شده: {sum(dropped.values())}\n\n")
        handle.write("## دلیل حذف\n\n")
        for reason, n in dropped.most_common():
            handle.write(f"- {reason}: {n}\n")
        handle.write("\n## شمارش به تفکیک بسته\n\n")
        for code, rows in sorted(by_book.items(), key=lambda x: -len(x[1])):
            handle.write(f"- `{code}`: {len(rows)} ردیف\n")
        handle.write("\n## فهرست کامل هر بسته\n\n")
        handle.write(
            "ستون `source_primary` هر ردیف هنوز لنگرگاه ندارد. نویسندهٔ هر کتابچه باید\n"
            "در بند متناظر، مبنای عدد را بنویسد و سپس شناسهٔ همین فهرست را جایگزین کند.\n\n"
        )
        for code, rows in sorted(by_book.items(), key=lambda x: -len(x[1])):
            handle.write(f"### {code} — {len(rows)} ردیف\n\n")
            handle.write("| id | indicator | value | unit | confidence |\n|---|---|---|---|---|\n")
            for row in rows:
                label = row["indicator"].replace("|", "／")
                handle.write(
                    f"| `{row['id']}` | {label} | {row['value']} | {row['unit']} | {row['confidence']} |\n"
                )
            handle.write("\n")

    print(f"ادغام: {len(merged)}  →  نگه‌داشته: {len(kept)}  حذف: {sum(dropped.values())}")
    print("دلیل حذف:")
    for reason, n in dropped.most_common():
        print(f"  {n:>5}  {reason}")
    print(f"\nنوشته شد:\n  {OUT_CSV}\n  {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
