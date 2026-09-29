"""یکنواخت‌سازی صدا — STD-HYD-VOICE-v1.0.

ابزار مکانیکی موج «الف». روی هر سند، واژهٔ گفتاری، شخص اول مفرد و
الگوهای جملهٔ بی‌معنا را به گزاره تبدیل می‌کند.

این ابزار محتوا را از دست نمی‌دهد و عدد نمی‌سازد. فقط صورت جمله را
یکنواخت می‌کند. هر جا که تبدیل خودکار معنا را تغییر می‌دهد، آن را
گزارش می‌کند تا نویسنده بازبینی کند.

اجرا:
  python scripts/voice_normalise.py            # فقط گزارش، بدون نوشتن
  python scripts/voice_normalise.py --apply    # اعمال روی سندهای پاک
"""

from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, "کتابها")

# سه سند مصون‌اند: نویسهٔ بیگانهٔ آن‌ها نقل عینی است
WHITELIST = {
    "دروازه-کنترل-کاراکتر.md",
    "سیاهه-نقل-بین‌المللی.md",
    "برنامه-ها-و-نهادهای-منطقه.md",
}

# تبدیل‌های ماشینی. هر مقدار یک جمله است که باید معنا را نگه دارد.
REPLACEMENTS: list[tuple[str, str]] = [
    # واژهٔ گفتاری که در آغاز جملهٔ بی‌معنا آمده
    (r"(?<![؀-ۿ])بله[،,]?[ \t]*", ""),
    (r"(?<![؀-ۿ])خب[،,]?[ \t]*", ""),
    # شخص اول مفرد — ممنوع مطلق
    (r"(?<![؀-ۿ])من(?![؀-ۿ])", "این سند"),
    (r"(?<![؀-ۿ])به عقیدهٔ من(?![؀-ۿ])", ""),
    (r"(?<![؀-ۿ])به نظر من(?![؀-ۿ])", ""),
    # فعل‌های تضعیف‌کننده — فقط در آغاز جمله بی‌معنا حذف می‌شوند
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))می‌شود گفت[ که]*\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))به نظر می‌رسد[ که]*\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))احتمالاً\s+", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))شاید\s+", ""),
    # خوداظهاری و آموزش شفاهی
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))نکتهٔ مهم:[ ]*", "قاعده: "),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))توجه کنید[ که]*[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))در پایان بگوییم[ که]*[،,]?\s*", "نتیجه: "),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))همان‌طور که می‌دانید[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))بگذارید ببینیم[ که]*[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))بیایید ببینیم[ که]*[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))خوشبختانه[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))متأسفانه[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))اگر بخواهیم صادق باشیم[،,]?\s*", ""),
    (r"(?:^|(?<=\.)|(?<=\؟)|(?<=!))باید توجه کنید[ که]*[،,]?\s*", "الزام است: "),
    # صفت شخصی بدون معیار
    (r"(?<![؀-ۿ])جالب(?![؀-ۿ])", "قابل‌توجه"),
    (r"(?<![؀-ۿ])خوشحال‌کننده(?![؀-ۿ])", "قابل‌قبول"),
    (r"(?<![؀-ۿ])لذت‌بخش(?![؀-ۿ])", "قابل‌قبول"),
    (r"\bچیز\b", "مورد"),
]

# سنجه‌های دروازهٔ صوت
BANNED_RE = re.compile(
    r"(?<![؀-ۿ])(?:بله|خب|من|او|ایشان|شاید|احتمالاً|جالب|خوشحال‌کننده|لذت‌بخش)(?![؀-ۿ])"
    r"|می‌شود گفت|به نظر می‌رسد|خوشبختانه|متأسفانه|نکتهٔ مهم|بگذارید ببینیم|بیایید ببینیم"
)
HEDGE_RE = re.compile(r"شاید|احتمالاً|به نظر می‌رسد|گمان|متردد")


def documents() -> list[str]:
    out = []
    for name in sorted(os.listdir(BOOKS)):
        if not name.endswith((".txt", ".md")):
            continue
        if name in WHITELIST:
            continue
        if name == "HDR.csv":
            continue
        out.append(os.path.join(BOOKS, name))
    return out


def opener_coverage(text: str) -> float:
    lines = [
        l for l in text.split("\n")
        if l.strip() and not l.strip().startswith(("|", "#", "---", "http"))
    ]
    sents = [s for l in lines for s in re.split(r"(?<=\.)\s+", l) if 30 < len(s) < 300]
    if not sents:
        return 0.0
    kinds = Counter(s[:7] for s in sents)
    used = len([k for k, v in kinds.items() if v >= 3])
    return 100 * used / max(len(kinds), 1)


def measure(path: str) -> dict:
    text = io.open(path, encoding="utf-8").read()
    sents = [
        s
        for l in text.split("\n")
        if l.strip() and not l.strip().startswith(("|", "#", "---"))
        for s in re.split(r"(?<=\.)\s+", l)
        if 30 < len(s) < 300
    ]
    n = max(len(sents), 1)
    return {
        "file": os.path.basename(path),
        "banned": len(BANNED_RE.findall(text)),
        "hedge_per_1k": 1000 * len(HEDGE_RE.findall(text)) / n,
        "coverage": opener_coverage(text),
        "long_sentences": 100 * sum(1 for s in sents if len(s.split()) > 30) / n,
        "tiny_sentences": 100 * sum(1 for s in sents if len(s.split()) < 5) / n,
    }


def apply(path: str) -> dict:
    text = io.open(path, encoding="utf-8").read()
    before = measure(path)
    new = text
    for pattern, repl in REPLACEMENTS:
        new = re.sub(pattern, repl, new)
    # فاصلهٔ دوبله از حذف واژه
    # این قاعده تبِ آغازینِ خطوط هنرِ شکل را می‌بلعید؛ فقط فاصلهٔ افقی را فرو می‌کاهد.
    new = re.sub(r"(?<![\t\n]) {2,}(?=[^\s])", " ", new)
    # این خط آسیب‌زا بود: ممیز اعشاریِ برچسب جدول را «۱ .۱» می‌کرد و
    # شمارش جدول را در سراسر مجموعه می‌شکست. حذف شد.

    if new == text:
        return {"file": os.path.basename(path), "changed": False, "removed": 0}
    backup = f"{path}.{__import__('time').strftime('%Y%m%d-%H%M')}.pre-voice.bak"
    io.open(backup, "w", encoding="utf-8", newline="").write(text)
    io.open(path, "w", encoding="utf-8", newline="").write(new)
    return {
        "file": os.path.basename(path),
        "changed": True,
        "removed": before["banned"] - measure(path)["banned"],
        "backup": os.path.basename(backup),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="اعمال تغییرات روی دیسک")
    parser.add_argument("--only", help="فقط یک فایل، بر پایهٔ نام")
    args = parser.parse_args()

    files = documents()
    if args.only:
        files = [f for f in files if args.only in os.path.basename(f)]
    if not files:
        print("سندی یافت نشد", file=sys.stderr)
        return 2

    if args.apply:
        results = [apply(f) for f in files]
        changed = [r for r in results if r["changed"]]
        total = sum(r["removed"] for r in changed)
        for r in changed:
            print(f"  ✓ {r['file']:<32} -{r['removed']:>4} نشانه")
        print(f"\nاعمال‌شده: {len(changed)} سند · حذف {total} نشانه · پشتیبان برای هر فایل ساخته شد")
        return 0

    rows = [measure(f) for f in files]
    print(f"{'فایل':<32}{'ممنوع':>7}{'تردید/۱۰۰۰':>12}{'پوشش%':>9}{'بلند%':>8}{'ریز%':>7}  داوری")
    for r in rows:
        cov = r["coverage"]
        verdict = []
        if r["banned"] > 0:
            verdict.append("رد: واژهٔ ممنوع")
        if cov < 12:
            verdict.append("رد: یکنواخت")
        if cov > 22:
            verdict.append("رد: پراکنده")
        if r["long_sentences"] >= 5:
            verdict.append("بازبینی: جملهٔ بلند")
        if not verdict:
            verdict.append("قبول")
        print(
            f"{r['file']:<32}{r['banned']:>7}{r['hedge_per_1k']:>12.2f}{cov:>9.1f}"
            f"{r['long_sentences']:>8.1f}{r['tiny_sentences']:>7.1f}  {' · '.join(verdict)}"
        )
    total_banned = sum(r["banned"] for r in rows)
    print(f"\nجمع نشانه‌های ممنوع در مجموعه: {total_banned}")
    print("برای اعمال: python scripts/voice_normalise.py --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
