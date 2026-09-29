"""Quick per-file size/dead-end probe for a single booklet (read-only).

Mirrors the sizing rule of scripts/audit_booklets.py: a chapter runs from its
`فصل N —` header to the next chapter header, so chapter 12 absorbs پیوست الف
and راهنمای اجرایی کشاورز.

اجرا:  python scripts/hp06_check.py
"""
from __future__ import annotations

import io
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "کتابها")
FLOORS = {1: 320, 2: 350, 3: 400, 4: 200, 5: 250, 6: 280,
          7: 170, 8: 200, 9: 350, 10: 450, 11: 280, 12: 250}
DEAD = ("فاقد شناسه", "تأییدنشده", "نیازمند خط پایه")
CLAIMS = ("مطابقت کامل با استاندارد", "تطبیق ۹۵", "۱۰۰٪ با استاندارد",
          "تنها راهکار", "تنها راه", "بالاتر از استاندارد", "موقعیت رقابتی منحصر",
          "بازدهی ۱۰۰", "نتیجه میدانی", "نتیجهٔ میدانی",
          "اندازه‌گیری‌شده در پایلوت", "همه پایلوت", "به دلیل ریسک حذف")
CHAP = re.compile(r"^(?:#{1,6}\s*)?فصل\s+([۰-۹]+)\s+—")
FA = "۰۱۲۳۴۵۶۷۸۹"
GATE = [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0xF900, 0xFAFF), (0x3040, 0x30FF),
        (0xAC00, 0xD7AF), (0x0400, 0x04FF), (0xFF01, 0xFF60), (0xFFFD, 0xFFFD),
        (0x0000, 0x001F)]


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "HP-06 لایه بندی خاک.txt"
    text = io.open(os.path.join(ROOT, name), encoding="utf-8").read()
    lines = text.split("\n")
    starts = []
    for i, line in enumerate(lines):
        m = CHAP.match(line)
        if m:
            starts.append((i + 1, int(m.group(1).translate(str.maketrans(FA, "0123456789")))))
    starts.append((len(lines) + 1, 99))
    sizes: dict[int, int] = {}
    for j in range(len(starts) - 1):
        if starts[j][1] in FLOORS:
            sizes[starts[j][1]] = starts[j + 1][0] - starts[j][0]
    print(f"{name}  ·  {len(lines)} سطر  ·  فصل {len(sizes)}  ·  کف ۴۰۰۰: "
          f"{'بله' if len(lines) >= 4000 else 'خیر'}")
    total = 0
    for k in sorted(FLOORS):
        if k in sizes:
            v = sizes[k]
            total += 1 if v >= FLOORS[k] else 0
            print(f"  فصل {k:>2}  {v:>5} سطر  کف {FLOORS[k]:>4}  "
                  f"{'بله' if v >= FLOORS[k] else f'کسر {FLOORS[k] - v}'}")
    print(f"  کف‌های برآورده: {total} از ۱۲")
    print(f"  بن‌بست: " + " · ".join(f"{d}={text.count(d)}" for d in DEAD if text.count(d)))
    print(f"  ادعای ممنوعه: " + " · ".join(f"{c}={text.count(c)}" for c in CLAIMS if text.count(c)))
    gate = sum(1 for ch in text for lo, hi in GATE
               if lo <= ord(ch) <= hi and ch not in "\n\t")
    print(f"  دروازهٔ کاراکتر: {gate}")
    print(f"  راهنمای کشاورز: {'بله' if 'راهنمای اجرایی کشاورز' in text else '—'}")
    for label, token in (("شکل", "شکل "), ("جدول", "جدول ")):
        print(f"  {label}: {text.count(token)}")
    print(f"  فرمول: {text.count('فرمول')}")
    print(f"  RR-06: {len(re.findall(r'RR-06-[0-9]+', text))}")
    print(f"  مدل: {len(re.findall(r'مدل [۰-۹]', text))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
