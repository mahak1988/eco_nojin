"""موج ۶ — ممیزی ارجاع متقاطع.

سه دسته ناسازگاری را که در مجموعه پنهان است پیدا می‌کند:

  الف) عدد متضاد       یک کمّیت که دو سند مقدار متفاوت برایش می‌دهند
  ب) عدد بدون رجیستر  عددی در متن که هیچ شناسه‌ای کنارش نیست
  ج) شناسهٔ بی‌مصرف    ردیف رجیستر که هیچ سندی به آن ارجاع نداده

خروجی متنی، با پیشنهاد نوشتن در فایل.

اجرا:  python scripts/audit_crossrefs.py [--json out.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "کتابها")
REGISTER = os.path.join(BOOKS, "_مرجع", "HDR.csv")

# سندهایی که ارقام برنامه را بیان می‌کنند و باید با رجیستر یکی باشند
VOLUMES = [
    "سند مرجع.txt",
    "مهندسی هیدروما.txt",
    "توجیهی فنی اقتصادی.txt",
    "راهنمای نقشه برداری.txt",
    "راهبردی هیدروما.txt",
    "بیزنس-پلن-شرکت.txt",
    "بیزنس-پلن-شرکت.md",
]

# کمّیت‌هایی که باید در سراسر مجموعه یک عدد داشته باشند
WATCHED = {
    "مجموع خدمات اکوسیستمی": r"(?:مجموع|جمع)\s+(?:کل\s+)?خدمات اکوسیستمی",
    "نسبت B/C برنامه": r"B\s*/\s*C",
    "نرخ داخلی": r"IRR|نرخ داخلی",
    "NPV": r"NPV|ارزش فعلی خالص",
    "دوره بازگشت": r"دوره\s+(?:بازگشت|بازگشت سرمایه)",
    "مساحت برنامه": r"۵۶۸[٬،, ]?۰۰۰|۵۶۸٬۴۰۰",
    "قیمت کربن": r"قیمت (?:پایه|کربن|ناخالص)[^\n]{0,30}?(\d+)\s*(?:دلار|USD)",
    "بودجه فاز ۱": r"۳٫?\d*\s*میلیون دلار|۳٬۱۵۰٬۰۰۰|۳٬۵۰۰٬۰۰۰",
}

# مقدار مصوب رجیستر برای هر کمّیت، تا گزارش بتواند ناسازگاری را نام ببرد
REGISTER_TRUTH = {
    "نسبت B/C برنامه": ("FN-21", "۲٫۲۱۹۳"),
    "مجموع خدمات اکوسیستمی": ("ES-07", "۶۲۹٫۹۵"),
    "نرخ داخلی": ("FN-28", "۱۰۲٫۳۴"),
    "NPV": ("FN-22", "۴۳۹٫۳۰۶"),
    "دوره بازگشت": ("FN-23", "۴٫۶۳"),
    "مساحت برنامه": ("SC-03", "۵۶۸٬۴۰۰"),
    "قیمت کربن": ("CB-02", "۲۵"),
}

ID_REF = re.compile(r"\b([A-Z]{1,5}-[0-9A-Z]{1,5}(?:-[0-9A-Z]{1,5})?)\b")
FA_DIGIT = "۰۱۲۳۴۵۶۷۸۹"


def read_register() -> dict[str, dict]:
    with open(REGISTER, encoding="utf-8") as handle:
        return {r["id"].strip(): r for r in csv.DictReader(handle)}


def all_documents() -> list[tuple[str, str]]:
    out = []
    for name in sorted(os.listdir(BOOKS)):
        if not name.endswith((".txt", ".md")) or name.startswith("HP-"):
            continue
        out.append((name, os.path.join(BOOKS, name)))
    for name in VOLUMES:
        path = os.path.join(BOOKS, name)
        if os.path.exists(path):
            out.append((name, path))
    return out


def numbers_near(text: str, pattern: str, window: int = 70) -> list[str]:
    found = []
    for match in re.finditer(pattern, text):
        seg = text[match.start() : match.start() + window]
        for num in re.findall(r"[۰-۹][۰-۹٬٫\u200c]*(?:[٫.][۰-۹]+)?", seg):
            found.append(num.replace("٬", "").replace("٫", "."))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    args = parser.parse_args()

    register = read_register()
    docs = all_documents()
    report: dict = {"contradictions": [], "unregistered": [], "unused_register_rows": []}

    # الف) عدد متضاد برای هر کمّیت تحت پایش
    for label, pattern in WATCHED.items():
        seen: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for name, path in docs:
            with open(path, encoding="utf-8") as _fh:
                text = _fh.read()
            for value in numbers_near(text, pattern):
                seen[value][name] += 1
        if len(seen) > 1:
            entry = {
                "quantity": label,
                "values": {
                    v: dict(f) for v, f in sorted(seen.items(), key=lambda x: -sum(x[1].values()))
                },
            }
            if label in REGISTER_TRUTH:
                ident, truth = REGISTER_TRUTH[label]
                entry["register_id"] = ident
                entry["register_value"] = truth
                if truth in register:
                    entry["register_value"] = register[ident]["value"]
            report["contradictions"].append(entry)

    # ج) شناسه‌های رجیستر که هیچ سندی ارجاع نداده
    used: set[str] = set()
    for _name, path in docs:
        with open(path, encoding="utf-8") as _fh:
            text = _fh.read()
        used.update(m for m in ID_REF.findall(text) if m in register)
    report["unused_register_rows"] = sorted(set(register) - used)

    # ب) ارجاع به شناسه‌ای که در رجیستر نیست
    for name, path in docs:
        with open(path, encoding="utf-8") as _fh:
            text = _fh.read()
        ghosts: dict[str, int] = defaultdict(int)
        for ident in ID_REF.findall(text):
            if ident not in register and not ident.startswith(("HP-0", "HP-1", "HP-2")):
                ghosts[ident] += 1
        for ident, n in sorted(ghosts.items(), key=lambda x: -x[1])[:20]:
            report["unregistered"].append({"file": name, "id": ident, "count": n})

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(f"نوشته شد: {args.json}")
        return 0

    print("=" * 92)
    print("الف) کمّیت‌هایی که چند مقدار متفاوت دارند")
    print("   برای هر کمّیت فقط سه مقدار پرتکرار و مقایسه با مقدار مصوب رجیستر")
    print("=" * 92)
    if not report["contradictions"]:
        print("  هیچ کمّیت تحت پایشی چند مقدار ندارد")
    for item in report["contradictions"]:
        print(f"\n  ▸ {item['quantity']}")
        total = sum(sum(f.values()) for f in item["values"].values())
        top = sorted(item["values"].items(), key=lambda x: -sum(x[1].values()))[:3]
        if len(item["values"]) > 3:
            print(
                f"      ({len(item['values'])} مقدار متفاوت در مجموع؛ سه مقدار پرتکرار از {total} ارجاع)"
            )
        for value, files in top:
            names = " · ".join(
                f"{k}({v})" for k, v in sorted(files.items(), key=lambda x: -x[1])[:5]
            )
            print(f"      {value:<18} {names}")
        if item.get("register_value"):
            print(f"      ← مصوب رجیستر: {item['register_value']}")

    print("\n" + "=" * 92)
    print(f"ب) ارجاع به شناسهٔ ثبت‌نشده — {len(report['unregistered'])} مورد")
    print("=" * 92)
    for row in report["unregistered"][:15]:
        print(f"  {row['count']:>4}×  {row['file']:<32} {row['id']}")
    if len(report["unregistered"]) > 15:
        print(f"  … و {len(report['unregistered']) - 15} مورد دیگر")

    print("\n" + "=" * 92)
    print(f"ج) ردیف رجیستر بدون ارجاع — {len(report['unused_register_rows'])} مورد")
    print("=" * 92)
    print(f"  نمونه: {' · '.join(report['unused_register_rows'][:20])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
