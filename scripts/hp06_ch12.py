"""Add بندهای ۱۲٫۴ تا ۱۲٫۶ to the HP-06 booklet and refresh the header asset line.

Pure UTF-8 text operation. The table and figure inventories are extracted from
the file itself, so the lists cannot drift from the body. The formula list is
extended for the twelve new chapter-3 models. Aborts without writing if the two
anchor lines are not unique.

اجرا:  python scripts/hp06_ch12.py
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "کتابها")
TARGET = os.path.join(ROOT, "HP-06 لایه بندی خاک.txt")
APX = "پیوست الف — ردیابی داده"
CH12_END = "26\tآموزش کشاورز درباره تقویم نگهداری\tجدول ۸.۱\tکشاورز\t□"
ASSET_ANCHOR = "دوره بازگشت: بازمحاسبهٔ بند ۹٫۴ — بدون خدمات اکوسیستمی بازگشتی رخ نمی‌دهد؛ با سهم خدمات اکوسیستمی ۸٫۳۰ سال"
ASSET_OLD = "۱۷ شکل + ۲۷ جدول + ۷ فرمول"
D = "[۰-۹٠-٩0-9]"
FIG_RE = re.compile(r"^شکل " + D)
TAB_RE = re.compile(r"^جدول " + D)

NEW_FORMULAS = [
    ("F8", "ΔS = P + Q_in − ET − Q_out − D", "تراز آب پروفیل لایه‌بندی‌شده", "۳٫۹٫۱"),
    ("F9", "q = K_aq × i × A", "ظرفیت لایهٔ ماسه", "۳٫۱۲٫۱"),
    ("F10", "h_c = ۲γ cos θ ÷ (ρ_w × g × r)", "بالایی موئینگی", "۳٫۱۴٫۱"),
    ("F11", "q ≤ ۰٫۱۰ × S_cap ÷ t", "شرط هیدرولیکی معیار شکستن", "۳٫۱۱٫۱"),
    ("F12", "d_k ≥ ۳ × d_a", "شرط هندسی معیار شکستن", "۳٫۱۱٫۱"),
    ("F13", "f(t) = fc + [f0 × (۱ − c) − fc] × e^(−k×t)", "نفوذ با جملهٔ پوسته", "۳٫۱۰٫۱"),
    ("F14", "f_v = (w_b ÷ ρ_b) ÷ [(w_b ÷ ρ_b) + (w_s ÷ ρ_s)]", "کسر حجمی بیوچار", "۳٫۱۳٫۱"),
    ("F15", "f_E = m × (۱ − Δa) × (۱ − r) + (۱ − m)", "کسر باقیماندهٔ تبخیر مالچ", "۳٫۱۵٫۱"),
    ("F16", "ρ_d(t) = ρ_d(0) + k_c × t", "زوال ساختار خاک", "۳٫۱۶٫۱"),
    ("F17", "ρ_b = ρ_s × (۱ − e)", "چگالی ظاهری و تخلخل", "۳٫۱۷٫۱"),
    ("F18", "A_surface = R × K × C × P", "فرسایش شیب ساخته‌شده", "۳٫۱۸٫۱"),
    ("F19", "ρ_d(n) = ρ_d(0) + Δρ × n", "تراکم ترافیک", "۳٫۱۹٫۱"),
    ("F20", "N(t) = N_0 × (۱ − d)^t", "عمر طراحی تحت کسری نگهداری", "۳٫۲۰٫۱"),
]

TAIL_HEAD = [
    "۱۲٫۴. فهرست جدول‌ها",
    "این فهرست، همهٔ جدول‌های این کتابچه را به ترتیب ظهور فهرست می‌کند. شمارش از متن استخراج شده است.",
]

TAIL_MID = [
    "۱۲٫۵. فهرست شکل‌ها",
    "این فهرست، همهٔ شکل‌های این کتابچه را به ترتیب ظهور فهرست می‌کند. شمارش از متن استخراج شده است.",
]

TAIL_TAIL = [
    "۱۲٫۶. جمع‌بندی فصل ۱۲",
    "فصل ۱۲ چهار بخش دارد: واژه‌نامه فنی با سی و یک ردیف، فهرست فرمول‌ها با بیست ردیف، چک‌لیست نهایی با بیست و شش ردیف، و دو فهرست کامل جدول‌ها و شکل‌ها. چهار بند جدید به این نسخه افزوده شد: فهرست جدول‌ها، فهرست شکل‌ها و این جمع‌بندی.",
    "سه گزارهٔ منفی این فصل صریح است. گزارهٔ یکم: واژه‌نامه سه اصطلاح کلیدی بندهای ۱٫۱ و ۲٫۴٫۱ و ۱٫۵ را ندارد و بندهای ۱٫۲۳ و ۲٫۲۵ افزودن آن‌ها را کار پایانی اعلام کرده‌اند. گزارهٔ دوم: چک‌لیست نهایی بیست و شش ردیف دارد ولی بیست و شش شمارهٔ بند ندارد و ارجاع آن به جدول‌هاست. گزارهٔ سوم: هیچ شمارهٔ استانداردی که در راستی‌آزمایی خوانده نشده، در فهرست فرمول‌ها و جدول‌ها نیامده است.",
    "جدول ۱۲٫۱۳ — سه گزارهٔ منفی فصل ۱۲ و بند پشتیبان",
    "گزاره — بند پشتیبان",
    "سه اصطلاح کلیدی در واژه‌نامه نیست — بند ۱٫۲۳",
    "چک‌لیست نهایی شمارهٔ بند ندارد — بند ۱۲٫۳",
    "شمارهٔ استاندارد خوانده‌نشده درج نمی‌شود — بند ۱۱٫۷",
    "جمع — سه گزاره؛ هر یک یک بند پشتیبان — سه بند نام‌برده",
    "منبع جدول ۱۲٫۱۳: بند ۱٫۲۳ و بند ۱۱٫۷ و بند ۱۲٫۳ و جدول ۱۲٫۱ و جدول ۱۲٫۲ — سطح اطمینان: B",
    "خلاصه فصل ۱۲",
    "فصل ۱۲ چهار بخش دارد. واژه‌نامه فنی سی و یک اصطلاح را تعریف می‌کند. فهرست فرمول‌ها بیست فرمول را با بخش مرجع می‌آورد. چک‌لیست نهایی بیست و شش گام اجرایی را با مسئول و تأیید می‌دهد. و دو فهرست کامل، همهٔ جدول‌ها و شکل‌های این کتابچه را با شمارش استخراج‌شده از متن فهرست می‌کنند.",
    "سه کار پایانی برای این فصل باقی مانده است: افزودن سه اصطلاح آب‌بند و پروفیل و تراکم به واژه‌نامه، تعیین تکلیف عدد ۲۵ مترمکعب خاک رس جدول ۲٫۷، و اصلاح عدد عمق کل پروفیل در بند ۱٫۱۱ به صد و بیست سانتی‌متر. هر سه در بندهای ۱٫۲۳ و ۲٫۲۵ و ۶٫۲۴ با مسئول نام‌برده ثبت شده‌اند.",
]


def main() -> int:
    with open(TARGET, encoding="utf-8") as _fh:
        text = _fh.read()
    if text.count(CH12_END) != 1 or text.count(ASSET_ANCHOR) != 1 or text.count(ASSET_OLD) != 0:
        print("لنگر یکتا نیست — نوشتن انجام نشد", file=sys.stderr)
        return 1
    head, rest = text.split(CH12_END, 1)
    _tail, apx = rest.split(APX, 1)

    lines = head.split("\n")
    figs = [l for l in lines if FIG_RE.match(l)]
    tabs = [l for l in lines if TAB_RE.match(l) and "—" in l]
    tabs = [l for l in tabs if not l.startswith("جدول ۲٫۷ هر") and not l.startswith("جدول ۸٫۱ یک")]
    tabs = [l for l in tabs if not l.startswith("جدول ۱۲٫۴") and not l.startswith("جدول ۱۲٫۵")]

    out = [CH12_END, *TAIL_HEAD]
    for i, t in enumerate(tabs, start=1):
        out.append(f"{i}\t{t}")
    out.append(f"جمع\t{len(tabs)} جدول در این کتابچه\t—\t—\tشمارش استخراج‌شده از متن")
    out.extend(TAIL_MID)
    for i, f in enumerate(figs, start=1):
        out.append(f"{i}\t{f}")
    out.append(f"جمع\t{len(figs)} شکل در این کتابچه\t—\t—\tشمارش استخراج‌شده از متن")
    out.extend(TAIL_TAIL)

    # extend the formula table
    marker = "F7\tBC_yield = Feedstock × Conversion_rate\tتولید بیوچار\t۲.۵.۱"
    if marker not in head:
        print("نشانگر فرمول یافت نشد — نوشتن انجام نشد", file=sys.stderr)
        return 1
    add = [f"{a}\t{b}\t{c}\t{d}" for a, b, c, d in NEW_FORMULAS]
    add.append(
        "جمع\t۲۰ فرمول در این کتابچه\t—\t—\tشش فرمول بندهای ۳٫۲ تا ۳٫۸ و چهارده فرمول بندهای ۳٫۹ تا ۳٫۲۰"
    )
    head = head.replace(marker, marker + "\n" + "\n".join(add), 1)

    new_body = "\n".join(out)
    asset = f"{len(figs)} شکل + {len(tabs)} جدول + ۲۰ فرمول"
    head = head.replace(ASSET_ANCHOR, ASSET_ANCHOR + "\n" + asset, 1)
    with open(TARGET, "w", encoding="utf-8", newline="") as _fh:
        _fh.write(head + new_body + "\n" + APX + apx)
    print(
        f"بند ۱۲٫۴ و ۱۲٫۵ و ۱۲٫۶ افزوده شد — جدول: {len(tabs)} · شکل: {len(figs)} · سطر دارایی: {asset}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
