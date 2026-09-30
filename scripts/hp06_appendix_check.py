"""Appendix A identifier-column validator for one booklet.

Mirrors the audit script's structural rule for the پیوست الف identifier column:
the header cell must be `شاخص` plus a tab, and every data row must carry a bare
register ID (or one of the approved placeholders) in the same column index.

اجرا:  python scripts/hp06_appendix_check.py
"""

from __future__ import annotations

import csv
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "کتابها")
REG = os.path.join(ROOT, "_مرجع", "HDR.csv")
APPROVED = {"—", "-", "بدون شناسهٔ مستقل", "جزء تشکیل‌دهنده"}
ID_PATTERN = re.compile(r"^[A-Z]{1,5}-[0-9A-Z]{1,5}(?:-[0-9A-Z]{1,5})?$")
SELF_ROW = re.compile(r"^تعداد |^بازهٔ زمانی|^شروع رسمی|^نرخ ارز مرجع")


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "HP-06 لایه بندی خاک.txt"
    with open(os.path.join(ROOT, name), encoding="utf-8") as _fh:
        text = _fh.read()
    with open(REG, encoding="utf-8") as _fh:
        known = {r["id"].strip() for r in csv.DictReader(_fh)}
    in_appendix = False
    id_index = -1
    rows = 0
    bad: list[str] = []
    for number, line in enumerate(text.split("\n"), start=1):
        if "پیوست الف — ردیابی داده" in line:
            in_appendix = True
        if in_appendix and "راهنمای اجرایی کشاورز" in line:
            in_appendix = False
        if not in_appendix or "\t" not in line:
            continue
        cells = [c.strip() for c in line.split("\t")]
        if cells and cells[0] == "شاخص":
            id_index = next((i for i, c in enumerate(cells) if c.startswith("شناسه")), -1)
            print(f"ستون شناسه در اندیس {id_index}")
            continue
        if id_index < 0 or len(cells) <= id_index:
            continue
        indicator, ident = cells[0], cells[id_index]
        if not indicator or SELF_ROW.search(indicator) or not ident:
            continue
        rows += 1
        if ident in APPROVED or (ID_PATTERN.match(ident) and ident in known):
            continue
        bad.append(f"L{number} {indicator[:40]} → {ident}")
    print(f"ردیف‌های بررسی‌شده: {rows}  ·  ناسازگار: {len(bad)}")
    for item in bad[:20]:
        print("  ", item)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
