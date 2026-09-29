"""موج صفر — اسکن بن‌بست‌های بدنهٔ فصل‌ها.

ابزار `build_hdr_candidates.py` فقط پیوست الف را می‌خواند. بیشتر بن‌بست‌های
مجموعه در بدنهٔ فصل‌ها نشسته‌اند، جایی که عدد در جمله یا سلول جدول آمده و
برچسب ممنوعه به آن چسبیده است. این ابزار هر دو را استخراج می‌کند و برای
هر مورد یک ردیف رجیستر کاندید می‌سازد.

خروجی: scripts/hdr_body_candidates.csv و scripts/hdr_body_candidates.md

این ابزار خودش در HDR.csv نمی‌نویسد. نوشتن بر عهدهٔ بازبینی انسانی است.

اجرا:  python scripts/scan_body_deadends.py
"""

from __future__ import annotations

import csv
import glob
import io
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOOKS = os.path.join(ROOT, "کتابها")
REGISTER = os.path.join(BOOKS, "_مرجع", "HDR.csv")
OUT_CSV = os.path.join(HERE, "hdr_body_candidates.csv")
OUT_MD = os.path.join(HERE, "hdr_body_candidates.md")

FIELDS = ["id", "domain", "indicator", "value", "unit", "source_primary", "year", "confidence", "consumers", "action", "status"]

# بند ۲٫۵ استاندارد STD-HYD-WRITE-v1.0
DEAD = ("فاقد شناسه", "تأییدنشده", "نیازمند خط پایه")

NUMBER = r"[۰-۹][۰-۹٬٫\u200c/]*(?:\.[۰-۹]+)?(?:\s*[–-]\s*[۰-۹][۰-۹٬٫\u200c/]*)?"
# برچسب پیش از عدد: چند واژهٔ فارسی که با «:» یا «—» یا جدی پایان می‌یابند
LABEL = r"(?:[\u0600-\u06FF\u200c]{2,}\s+){0,6}?[\u0600-\u06FF\u200c]{2,}"
UNIT = r"(?:دلار|متر|سانتی‌متر|میلی‌متر|میلی‌متر|کیلوگرم|تن|هکتار|درصد|روز|ماه|سال|ساعت|لیتر|درجه|نور|بر|کیلووات|سانتی|هوا|ها|بذر|گره|رغز|تن بر|کیلووات\u200cساعت)"
PACKAGE = re.compile(r"^HP-(\d+)")

DOMAIN_HINT = {
    "قیمت": ("قیمت", "PR"), "هزینه": ("مالی", "FN"), "نرخ": ("مالی", "FN"),
    "بازگشت": ("مالی", "FN"), "B/C": ("مالی", "FN"), "نسبت": ("مالی", "FN"),
    "CAPEX": ("مالی", "FN"), "OPEX": ("مالی", "FN"),
    "مساحت": ("مقیاس", "SC"), "هکتار": ("مقیاس", "SC"), "سطح": ("مقیاس", "SC"),
    "خدمات اکوسیستمی": ("خدمات اکوسیستمی", "ES"), "گرده": ("خدمات اکوسیستمی", "ES"),
    "ترسیب": ("خدمات اکوسیستمی", "ES"), "کربن": ("کربن", "CB"),
    "استاندارد": ("استاندارد", "ST"), "ISO": ("استاندارد", "ST"), "آزمون": ("استاندارد", "ST"),
    "مدل": ("مدل شبیه‌سازی", "MD"), "RUSLE": ("مدل شبیه‌سازی", "MD"), "WEPP": ("مدل شبیه‌سازی", "MD"),
    "پایلوت": ("پایلوت", "PL"), "PL-": ("پایلوت", "PL"),
    "آمار": ("آمار ملی", "NS"),
    "بذر": ("گونه", "SP"), "گونه": ("گونه", "SP"), "درخت": ("گونه", "SP"), "بوته": ("گونه", "SP"),
    "سنگ": ("مواد", "M"), "چوب": ("مواد", "M"), "لوله": ("مواد", "M"), "خاک": ("مواد", "M"),
    "مالچ": ("مواد", "M"), "ماده": ("مواد", "M"),
    "حسگر": ("تجهیزات", "EM"), "آبشخور": ("تجهیزات", "EM"), "شیر": ("تجهیزات", "EM"),
    "ریسک": ("ریسک", "R"), "خطر": ("ریسک", "R"), "خرابی": ("ریسک", "R"),
    "سهم": ("حکمرانی", "GV"), "کارگروه": ("حکمرانی", "GV"), "کمیته": ("حکمرانی", "GV"),
    "تنوع": ("محیط زیست", "S"), "محیط": ("محیط زیست", "S"),
    "ارز": ("هدف فنی", "TO"), "هدف": ("هدف فنی", "TO"),
}


def guess_domain(text: str) -> tuple[str, str]:
    for needle, pair in DOMAIN_HINT.items():
        if needle in text:
            return pair
    return "هدف فنی", "TO"


def split_cells(line: str) -> list[str]:
    return [c.strip() for c in line.split("\t")]


def harvest(text: str, code: str) -> list[dict]:
    """هر بن‌بست بدنه را با برچسب، مقدار و واحدش استخراج می‌کند."""
    out: list[dict] = []
    lines = text.split("\n")
    seen: set[str] = set()

    for number, line in enumerate(lines, start=1):
        if not any(mark in line for mark in DEAD):
            continue

        cells = split_cells(line)
        # حالت جدول: شناسه در یک سلول و مقدار در سلول کنار آن
        if len(cells) >= 3:
            for i, cell in enumerate(cells):
                if not any(mark in cell for mark in DEAD):
                    continue
                label = cells[0] if i else ""
                value = cells[1] if len(cells) > 1 else ""
                unit = cells[2] if len(cells) > 2 else ""
                if not re.search(r"\d|[۰-۹]", value):
                    continue
                key = f"{label}|{value}|{unit}"
                if not label or key in seen:
                    continue
                seen.add(key)
                out.append(_row(label, value, unit, code, number))
            continue

        # حالت جمله: برچسب و مقدار پیش از بن‌بست در همان جمله
        for mark in DEAD:
            for match in re.finditer(re.escape(mark), line):
                left = line[max(0, match.start() - 90): match.start()]
                number_match = None
                for candidate in reversed(list(re.finditer(NUMBER, left))):
                    number_match = candidate
                    break
                if not number_match:
                    continue
                value = number_match.group(0).strip()
                label_part = left[: number_match.start()].strip(" \t—–-:()[]«»")
                label = re.sub(r"\s+", " ", label_part)[-70:].strip()
                if len(label) < 4 or label in seen:
                    continue
                tail = line[match.end(): match.end() + 40]
                unit_match = re.match(rf"\s*({UNIT})", tail)
                unit = unit_match.group(1) if unit_match else ""
                seen.add(label)
                out.append(_row(label, value, unit, code, number))
    return out


def _row(label: str, value: str, unit: str, code: str, line_no: int) -> dict:
    domain, family = guess_domain(f"{label} {unit}")
    return {
        "id": "",
        "domain": domain,
        "indicator": label,
        "value": value,
        "unit": unit or "—",
        "source_primary": "— باید در بند متناظر نوشته شود",
        "year": "۱۴۰۵",
        "confidence": "C",
        "consumers": code,
        "action": f"نوشتن مبنای عدد در بند متناظر — فعلاً بدون لنگرگاه (سطر {line_no})",
        "status": "ثبت شد",
        "_family": family,
        "_line": line_no,
    }


def main() -> int:
    if not os.path.isdir(BOOKS):
        print(f"پوشه پیدا نشد: {BOOKS}", file=sys.stderr)
        return 2

    with open(REGISTER, encoding="utf-8") as handle:
        taken = {r["id"].strip() for r in csv.DictReader(handle)}

    rows: list[dict] = []
    per_book: dict[str, int] = {}
    for path in sorted(glob.glob(os.path.join(BOOKS, "HP-*.txt"))):
        name = os.path.basename(path)
        match = PACKAGE.match(name)
        if not match:
            continue
        code = f"HP-{match.group(1)}"
        text = io.open(path, encoding="utf-8").read()
        found = harvest(text, code)
        per_book[code] = len(found)
        rows.extend(found)

    # شاخص تکراری بین بسته‌ها یکتا می‌شود
    spread: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        spread[row["indicator"]].add(row["consumers"])
    for row in rows:
        if len(spread[row["indicator"]]) > 1:
            row["indicator"] = f"{row['indicator']} — {row['consumers']}"

    counters: dict[str, int] = defaultdict(int)
    used: set[str] = set()
    for row in rows:
        family = row.pop("_family")
        line_no = row.pop("_line")
        while True:
            counters[family] += 1
            new_id = f"{family}-{counters[family]:02d}"
            if new_id not in taken and new_id not in used:
                break
        row["id"] = new_id
        used.add(new_id)
        row["action"] = f"نوشتن مبنای عدد در بند متناظر — فعلاً بدون لنگرگاه (سطر {line_no})"

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in FIELDS})

    with open(OUT_MD, "w", encoding="utf-8") as handle:
        handle.write("# بن‌بست‌های بدنهٔ فصل‌ها — فهرست لنگرکردن\n\n")
        handle.write(f"تعداد کل: **{len(rows)}**\n\n")
        handle.write("## تفکیک بر پایهٔ بسته\n\n")
        for name, n in sorted(per_book.items(), key=lambda x: -x[1]):
            if n:
                handle.write(f"- `{name}`: {n}\n")
        handle.write("\n## تفکیک بر پایهٔ حوزه\n\n")
        for domain, n in Counter(r["domain"] for r in rows).most_common():
            handle.write(f"- {domain}: {n}\n")
        handle.write(
            "\n## قاعدهٔ کار\n\n"
            "هر ردیف یک عدد است که در بدنهٔ کتابچه آمده و برچسب ممنوعه به آن چسبیده است.\n"
            "وظیفهٔ نویسنده: رفتن به بند متناظر و نوشتن یکی از سه چیز — محاسبهٔ نشان‌داده‌شده،\n"
            "دلیل انتخاب، یا پروتکل اندازه‌گیری — و سپس جایگزینی برچسب ممنوعه با این شناسه.\n"
        )

    print(f"بن‌بست‌های بدنه: {len(rows)}")
    print(f"نوشته شد:\n  {OUT_CSV}\n  {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
