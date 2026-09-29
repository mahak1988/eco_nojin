"""رفع فساد بایت NUL و یکسان‌سازی سرفصل فصل‌ها در یک کتابچه.

کارگر نگارش HP-15 هنگام نرمال‌سازی CRLF با Array.Copy اشتباه، بایت NUL
وارد فایل کرد. این ابزار فساد را برطرف می‌کند، سطرهای NUL را حذف می‌کند،
و پیشوند Markdown را از سرفصل فصل‌ها برمی‌دارد تا قالب با بقیهٔ مجموعه
یکسان شود.

اجرا:  python scripts/repair_nulls.py "کتابها\HP-15 شوری و زهکشی.txt"
"""

from __future__ import annotations

import io
import os
import re
import sys
import time


def main() -> int:
    if len(sys.argv) < 2:
        print("کاربرد: repair_nulls.py <مسیر فایل>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
    if not os.path.exists(path):
        print(f"یافت نشد: {path}", file=sys.stderr)
        return 2

    raw = open(path, "rb").read()
    nul_count = raw.count(b"\x00")
    backup = f"{path}.{time.strftime('%Y%m%d-%H%M')}.pre-repair.bak"
    open(backup, "wb").write(raw)

    text = raw.decode("utf-8", errors="replace")
    # بایت NUL و نویسهٔ جایگزینِ ناشی از آن
    text = text.replace("\x00", "").replace("�", "")
    # سطرهایی که پس از حذف NUL خالی شدند و تنها از نویسهٔ کنترلی ساخته شده بودند
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # یکسان‌سازی سرفصل فصل‌ها: حذف پیشوند Markdown و فاصلهٔ اضافه
    text = re.sub(r"^#{1,6}\s*(فصل\s+[\u06F0-\u06F9]+\s+—)", r"\1", text, flags=re.M)

    lines = [ln.rstrip() for ln in text.split("\n")]
    # حذف سطرهای کاملاً خالیِ انباشته در انتهای فایل
    while lines and not lines[-1].strip():
        lines.pop()
    if lines:
        lines.append("")

    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write("\r\n".join(lines))

    check = open(path, "rb").read()
    after_nul = check.count(b"\x00")
    print(f"بایت NUL پیش از تعمیر: {nul_count}  ·  پس از تعمیر: {after_nul}")
    print(f"سطرها: {len(lines)}  ·  اندازه: {len(check)} بایت")
    print(f"پشتیبان: {os.path.basename(backup)}")
    if after_nul:
        print("⛔ فساد باقی است", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
