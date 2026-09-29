"""موج صفر — درج ردیف‌های پیش‌نویس در رجیستر اصلی HDR.csv.

پیش از اجرا باید نسخهٔ پشتیبان ساخته شود.
"""

from __future__ import annotations

import csv
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(ROOT, "کتابها", "_مرجع", "HDR.csv")
DRAFT = os.path.join(ROOT, "scripts", "HDR_draft.csv")
FIELDS = ["id", "domain", "indicator", "value", "unit", "source_primary", "year", "confidence", "consumers", "action", "status"]

UNANCHORED = ("بدون لنگرگاه", "بی‌لنگرگاه", "متناظر", "—")


def main() -> int:
    if not os.path.exists(DRAFT):
        print(f"پیش‌نویس یافت نشد: {DRAFT}", file=sys.stderr)
        return 2

    with open(REGISTER, encoding="utf-8") as handle:
        old = list(csv.DictReader(handle))
    with open(DRAFT, encoding="utf-8") as handle:
        new = list(csv.DictReader(handle))

    taken = {r["id"] for r in old}
    collisions = [r for r in new if r["id"] in taken]
    if collisions:
        print(f"⛔ {len(collisions)} تصادم شناسه — درج متوقف شد:", file=sys.stderr)
        for r in collisions[:5]:
            print(f"   {r['id']} — {r['indicator'][:60]}", file=sys.stderr)
        return 1

    for row in new:
        row["status"] = "ثبت شد"
        if any(mark in row["source_primary"] for mark in UNANCHORED):
            row["source_primary"] = "نیازمند لنگرگاه بند — موج صفر"
        if not row["action"]:
            row["action"] = "نوشتن مبنای عدد در بند متناظر"

    with open(REGISTER, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in old + new:
            writer.writerow({k: row.get(k, "") for k in FIELDS})

    with open(REGISTER, encoding="utf-8") as handle:
        check = list(csv.DictReader(handle))
    ids = [r["id"] for r in check]
    print(f"رجیستر پیش از درج: {len(old)} ردیف")
    print(f"درج‌شده: {len(new)} ردیف")
    print(f"رجیستر پس از درج: {len(check)} ردیف")
    print(f"شناسهٔ تکراری: {len(ids) - len(set(ids))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
