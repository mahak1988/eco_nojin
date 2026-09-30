"""بررسی نهایی حذف سطر کربن از درآمد مستقیم.

اجرا: python scripts/_carbon_final_check.py
"""

from __future__ import annotations

BOOKS = r"D:\eco_nojin\کتابها"
FILES = ["بیزنس-پلن-شرکت.txt", "بیزنس-پلن-شرکت.md", "سند مرجع.txt"]

GATE = {
    "CJK-ideograph": (0x4E00, 0x9FFF),
    "CJK-ext-A": (0x3400, 0x4DBF),
    "CJK-compat": (0xF900, 0xFAFF),
    "kana": (0x3040, 0x30FF),
    "hangul": (0xAC00, 0xD7AF),
    "cyrillic": (0x0400, 0x04FF),
    "halfwidth": (0xFF01, 0xFF60),
    "replacement": (0xFFFD, 0xFFFD),
    "NUL": (0x0000, 0x0000),
    "C0-control": (0x0001, 0x0008),
    "C0-control-2": (0x000B, 0x000C),
    "C0-control-3": (0x000E, 0x001F),
}

FORBIDDEN = ["فاقد شناسه", "تأییدنشده", "نیازمند خط پایه", "ثبت‌نشده در HDR"]
KEEP = {
    "بیزنس-پلن-شرکت.txt": [
        "EN-BP-1405",
        "در حال ثبت — قالب حقوقی نهایی تعیین نشده است",
        "۱۰۰٬۰۰۰ تومان بر دلار",
        "۱۰ سال",
        "۱۰٪",
        "مبنای رجیستر",
        "معادل دو نگارش",
        "اکو نوژین ۵۶۸٬۴۰۰ هکتار را خودش اجرا نمی‌کند",
        "پایان سند بیزنس‌پلن شرکت اکو نوژین",
        "جالیزان هوشمند پارس",
        "ریسک ۲۰",
        "ریسک ۱۹",
    ],
    "بیزنس-پلن-شرکت.md": [
        "EN-BP-1405",
        "در حال ثبت — قالب حقوقی نهایی تعیین نشده است",
        "۱۰۰٬۰۰۰ تومان بر دلار",
        "۱۰ سال",
        "۱۰٪",
        "مبنای رجیستر",
        "معادل دو نگارش",
        "پایان سند · نسخهٔ ۱٫۰",
        "جلالیزان هوشمند پارس",
        "ریسک ۲۰",
        "ریسک ۱۹",
    ],
    "سند مرجع.txt": ["ES-37", "ES-38", "ES-39", "ES-40", "۶۲۹٫۹۵", "۳۵۸٫۰۶۴"],
}
NEW = ["ES-37", "ES-38", "ES-39", "ES-40", "CB-03", "CB-04", "CB-05", "CB-06", "ISO 14064", "Verra"]


def gate_hits(text: str) -> dict[str, int]:
    return {n: sum(1 for c in text if lo <= ord(c) <= hi) for n, (lo, hi) in GATE.items()}


def main() -> int:
    bad = 0
    for name in FILES:
        with open(f"{BOOKS}\\{name}", encoding="utf-8") as _fh:
            text = _fh.read()
        print(f"\n=== {name} — {len(text.split(chr(10)))} lines ===")
        hits = {k: v for k, v in gate_hits(text).items() if v}
        print(f"  char gate      : {'FAIL ' + str(hits) if hits else 'OK — zero hits'}")
        bad += bool(hits)
        found = {f: text.count(f) for f in FORBIDDEN if text.count(f)}
        print(f"  forbidden      : {found if found else 'OK — zero'}")
        bad += bool(found)
        miss = [k for k in KEEP[name] if k not in text]
        print(f"  kept strings   : {'MISSING ' + str(miss) if miss else 'all present'}")
        bad += bool(miss)
        print("  new ids        : " + " · ".join(f"{k}={text.count(k)}" for k in NEW))
    print(f"\nTOTAL PROBLEMS: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
