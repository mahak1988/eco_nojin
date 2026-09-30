"""ممیزی ساختاری کتابچه‌های طرح هیدروما نوژین.

برای هر فایل `HP-XX *.txt` در `کتابها/` بررسی می‌کند:
  - تعداد سطر در برابر کف ۴۰۰۰
  - تعداد فصل با بدنه در برابر کف ۱۲
  - اندازهٔ هر فصل در برابر کف سطری قرارداد توسعه
  - وجود پیوست الف، راهنمای اجرایی کشاورز و سطر پایان
  - دروازهٔ کنترل کاراکتر
  - عبارت‌های ممنوعهٔ بند ۷ قواعد یکپارچه‌سازی

اجرا:  python scripts/audit_booklets.py
خروجی: جدول متنی. با --json خروجی ساختاریافته.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "کتابها")

HERE = os.path.dirname(os.path.abspath(__file__))
# ROOT خودش پوشهٔ «کتابها» است. افزودن دوبارهٔ «کتابها» مسیر را خراب می‌کند —
# همان اشکالی که دو بار در همین فایل رخ داده بود.
BOOKS = ROOT

LINE_FLOOR = 4000

# بند ۶٫۱ استاندارد STD-HYD-WRITE-v1.0 — نسخهٔ اصلاح‌شده.
# کف‌های نخستین جمعشان ۷۱۰۰ می‌شد، یعنی ۹۵ درصد بیشتر از الزام ۴۰۰۰؛
# کف ابزار توزیع است نه ابزار افزایش.
CHAPTER_FLOORS = {
    1: 320,
    2: 350,
    3: 400,
    4: 200,
    5: 250,
    6: 280,
    7: 170,
    8: 200,
    9: 350,
    10: 450,
    11: 280,
    12: 250,
}

# دروازهٔ کنترل کاراکتر — دروازه-کنترل-کاراکتر.md
GATE_RANGES = {
    "CJK-ideograph": (0x4E00, 0x9FFF),
    "CJK-ext-A": (0x3400, 0x4DBF),
    "CJK-compat": (0xF900, 0xFAFF),
    "kana": (0x3040, 0x30FF),
    "hangul": (0xAC00, 0xD7AF),
    "cyrillic": (0x0400, 0x04FF),
    "halfwidth": (0xFF01, 0xFF60),
    "replacement": (0xFFFD, 0xFFFD),
    # نویسه‌های کنترلی C0 به‌جز سطر جدید و تب. یک بار ۸۶۲۴۷ بایت NUL
    # از یک نرمال‌سازی CRLF نادرست وارد یک کتابچه شد و از دروازه رد شد،
    # چون بازهٔ NUL در فهرست بالا نبود.
    "NUL": (0x0000, 0x0000),
    "C0-control": (0x0001, 0x0008),
    "C0-control-2": (0x000B, 0x000C),
    "C0-control-3": (0x000E, 0x001F),
}

# بند ۷ قواعد یکپارچه‌سازی. تطبیق رشته‌ای به‌تنهایی کافی نیست و سه طبقه دارد:
#   نقض        — ادعای زنده بدون معیار و بدون بافت نفی یا ممنوعیت
#   فنی-محدود  — «تنها راه» با دامنهٔ صریح؛ هویت فنی است نه ادعای رقابتی
#   نفی-ممنوعی — در بافت نفی، گزارش حذف، یا جدول خوداظهاری
# فقط طبقهٔ «نقض» دروازه را رد می‌کند.
BANNED_CLAIMS = [
    "مطابقت کامل با استاندارد",
    "تطبیق ۹۵",
    "۱۰۰٪ با استاندارد",
    "تنها راهکار موجود",
    "تنها راهکار",
    "تنها راه",
    "بالاتر از استاندارد",
    "موقعیت رقابتی منحصر",
    "بازدهی ۱۰۰",
    "نتیجه میدانی",
    "نتیجهٔ میدانی",
    "اندازه‌گیری‌شده در پایلوت",
    "همه پایلوت",
    "به دلیل ریسک حذف",
]

# نشانه‌های بافت نفی یا ممنوعیت — وجود هر کدام، خط را از طبقهٔ نقض خارج می‌کند.
NEGATION_MARKERS = (
    "ممنوع",
    "حذف شد",
    "حذف‌شده",
    "حذف نشده",
    "حذف ادعا",
    "نیاید",
    "نباید",
    "بند ۷",
    "قاعدهٔ سازه",
    "در برابر",
    "جایگزین",
    "پرهیز",
    "نه ",
    "نیست",
    "نمی‌شود",
    "نمی‌شوند",
    "نمی‌کنند",
    "هیچ",
    "صفر",
    "بازتولیدپذیر",
    "خوداظهار",
    "فهرست",
    # بافتِ «این عبارت را نمی‌نویسیم» و «این مورد را اصلاح کردیم» نقض نیست.
    # بدون این نشانه‌ها، سندی که فهرست ممنوعیت‌های خودش را می‌آورد،
    # و سندی که اصلاحاتش را ثبت می‌کند، هر دو نقض گزارش می‌شدند.
    "نوشته نمی‌شود",
    "نمی‌نویس",
    "تبدیل شد",
    "محدود با",
    "بازنگری شد",
    "اصلاح شد",
    "حذف یا بازنویسی شده",
    "بازنویسی شده",
    "حذف شده",
    "به ادعای مهندسی",
    "به مقایسهٔ عددی",
)

# «تنها راه» وقتی فنی-محدود است که دامنهٔ صریح داشته باشد.
BOUNDED_MARKERS = (
    "در C",
    "در سطح",
    "در مقطع",
    "در حالت",
    "در این",
    "به‌عنوان تنها راه",
    "در اقلیم",
    "برای",
    "تحت",
)

# بند ۲ استاندارد STD-HYD-WRITE-v1.0 — رشته‌هایی که دیگر مجاز نیستند.
# هر کدام که در متن بیاید، دروازه را رد می‌کند.
#
# این فهرست به‌تنهایی کافی نیست و نباید تنها سازوکار باشد. یک کارگر نگارش
# رشتهٔ تازه‌ای به نام «ثبت‌نشده در HDR — نیازمند ثبت توسط R2» ساخت و ۱۶۸ بار
# به کار برد؛ فهرست رشته‌ای آن را نمی‌دید. بنابراین قاعدهٔ ساختاریِ
# check_id_column زیر کار می‌کند و این فهرست فقط لایهٔ نخست است.
FORBIDDEN_STRINGS = {
    "فاقد شناسه": "بند ۱٫۱ استاندارد — عدد بدون شناسهٔ رجیستر ممنوع",
    "تأییدنشده": "بند ۲٫۵ استاندارد — بن‌بست به‌جای پاسخ ممنوع",
    "نیازمند خط پایه": "بند ۲٫۴ استاندارد — بدون پروتکل اندازه‌گیری ممنوع",
    "ثبت‌نشده در HDR": "بند ۱٫۱ استاندارد — شناسه باید تخصیص یافته باشد، نه اینکه به تعویق بیفتد",
    "نیازمند ثبت توسط": "بند ۱٫۱ استاندارد — همان تعویق، با عبارت دیگر",
    "پیشنهاد شناسه جدید": "بند ۱٫۱ استاندارد — شناسه ساخته و درج می‌شود، پیشنهاد کافی نیست",
    "نیازمند سه استعلام": "بند ۲٫۳ استاندارد — باید پروتکل استعلام کامل بیاید، نه اشاره",
}

# مقادیر مجاز در ستون شناسه: یک شناسهٔ رجیستر، یا خالی، یا یکی از این‌ها
APPROVED_ID_VALUES = {"—", "-", "بدون شناسهٔ مستقل", "جزء تشکیل‌دهنده"}
# خانوادهٔ شناسه می‌تواند یک تا پنج حرف باشد: رجیستر چهار خانوادهٔ تک‌حرفی
# دارد (M=130، R=31، S=19، G=4) که با {2,5} رد می‌شدند و ۱۸۴ شناسهٔ معتبر
# به‌اشتباه بن‌بست شمرده می‌شدند. آزمون اصلی، وجود در رجیستر است؛ الگو فقط
# پیش‌شرط ارزان آن است، پس باید سخاوتمندانه باشد نه سخت‌گیرانه.
ID_PATTERN = re.compile(r"^[A-Z]{1,5}-[0-9A-Z]{1,5}(?:-[0-9A-Z]{1,5})?$")
# سرفصل فصل باید سطر مستقل باشد. یک سطر جدول که سلول نخستش با «فصل ۲ —»
# شروع می‌شود — مثل جدول تقویم فصلی — سرفصل نیست. تب، سطر را قطعی می‌کند.
_CH_HEADING = re.compile(r"^فصل\s+([۰-۹]+)\s+—")
_CH_LOOSE = re.compile(r"^فصل\s+([۰-۹]+)\s+—")
_FA = "۰۱۲۳۴۵۶۷۸۹"
_MAP = str.maketrans(_FA, "0123456789")
ID_HEADER = re.compile(r"^شاخص\t")

# ردیف‌هایی که خوداظهاری‌اند و شناسه ندارندن
SELF_ROW = re.compile(r"^تعداد |^بازهٔ زمانی|^شروع رسمی|^نرخ ارز مرجع")
# نشان ردیف مغایرت — تنها با این نشانه مجاز است متن به‌جای شناسه بنشیند
CONTRA_MARK = "🔴"


def table_census(text: str) -> dict[str, int]:
    """شمار سطر هر جدول شماره‌گذاری‌شده.

    این سنجه برای یک نقطهٔ کور ساخته شد: یک جایگزینی دسته‌ای که رشتهٔ
    جست‌وجویش به نویسهٔ خط جدید ختم می‌شد، سطرها را به هم چسباند و سه جدول
    را در یک سطر فرو کشید — ۳۰ سطر محتوا ناپدید شد، در حالی که شمار
    بن‌بست و سلول نامعتبر هر دو صفر ماندند. دروازه نمی‌تواند نبودِ محتوا را
    ببیند مگر بشمارد. پس می‌شمارد.

    یک بررسی دیگر هم دارد: اگر یک سطر بیش از سه بار تکرار شده باشد، آن
    جدول فروپاشیده است. جدول سالم هرگز یک سطر را تکرار نمی‌کند.
    """
    census: dict[str, int] = {}
    per_table_seen: dict[str, set[str]] = {}
    per_table_len: dict[str, list[int]] = {}
    current = None
    # برچسب جدول گاهی با خط تیره جدا می‌شود و گاهی با تب — «جدول ۳.۱ — عنوان»
    # در برابر «جدول ۳.۱<TAB>عنوان». هر دو باید شناخته شوند، وگرنه شمارش
    # سطر آن جدول صفر گزارش می‌شود و افت ساختگی می‌سازد.
    header = re.compile(r"^\s*(?:جدول|شکل)\s+([۰-۹\d]+[٫٬.][۰-۹\d]+)\s*(?:[-—:،]|\t|$)")
    for line in text.split("\n"):
        match = header.match(line)
        if match:
            current = match.group(1)
            census.setdefault(current, 0)
            per_table_seen.setdefault(current, set())
            per_table_len.setdefault(current, [])
            continue
        if current and ("\t" in line or line.strip().startswith("|")):
            census[current] += 1
            per_table_seen[current].add(line.strip())
            per_table_len[current].append(len(line.strip()))
        elif current and not line.strip():
            continue
        elif current:
            current = None

    # جدول فروپاشیده: چند سطر به یکی چسبیده‌اند.
    # امضای نخست تکرار سطر است؛ امضای دوم طول است. سطر فروپاشیده یکتاست
    # و تکرار نمی‌شود، پس تکرار به‌تنهایی آن را نمی‌بیند.
    for table, seen in per_table_seen.items():
        lengths = sorted(per_table_len.get(table, []))
        if not lengths:
            continue
        median = lengths[len(lengths) // 2] or 1
        longest = lengths[-1]
        repeated = census.get(table, 0) - len(seen)
        oversized = 1 if longest > 3 * median and median > 40 else 0
        lost_rows = repeated + oversized
        if lost_rows >= 2:
            census[table] = -lost_rows
    return census


def _key(table: str) -> str:
    """کلید شمارش، بی‌تفاوت به جداکنندهٔ اعشار.

    چند فایل هر دو جداکننده را به کار می‌برند — HP-04 صد و بیست و هشت جدول با
    نقطهٔ لاتین و صد و چهارده با جداکنندهٔ عربی. بدون این نرمال‌سازی، شمارش
    تفاوت نماییِ یک جدول را «حذف» گزارش می‌کند.
    """
    return table.replace("٫", ".").replace("٬", ".").replace(" ", "")


def census_drift(path: str, census: dict[str, int]) -> list[str]:
    """فهرست جدول‌هایی که سطرشان کم شده — نشانهٔ محتوای ناپدیدشده."""
    base_path = os.path.join(HERE, "table_census_baseline.csv")
    if not os.path.exists(base_path):
        return []
    baseline: dict[tuple[str, str], int] = {}
    with open(base_path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            baseline[(_key(row["file"]), _key(row["table"]))] = int(row["rows"])
    name = os.path.basename(path)
    current = {_key(t): n for t, n in census.items()}
    lost, shrunk = [], []
    for (file_name, table), base_rows in sorted(baseline.items()):
        if file_name != name:
            continue
        if table not in current:
            lost.append(f"{table}: {base_rows} سطر — حذف یا برچسب‌گذاری دوباره")
        elif current[table] < 0:
            lost.append(
                f"{table}: {base_rows} سطر، {abs(current[table])} سطر تکراری — جدول فروپاشیده"
            )
        elif current[table] < base_rows:
            shrunk.append(f"{table}: {base_rows} → {current[table]}")
    return lost + shrunk


def duplicate_lines(text: str, minimum: int = 40) -> list[str]:
    """خطوط تکراریِ دقیق و بلند را برمی‌گرداند.

    سنجهٔ پُرشدگی است، نه شمار تکرار. سه دسته تکرار عامدانه‌اند و باید از این
    سنجه بیرون بمانند؛ حذفشان یعنی حذف ساختار یا از بین بردن یکدستی:

      الف) اجرای گلیف — خط کادرکشی، خط زیرین، و ردیف جدولِ کادرکشی. اینها
         ساختار تصویری‌اند و در هر بلوک تکرار می‌شوند.
      ب) سطر ارجاع به استاندارد — در هر سند یکسان است، درست مثل جدول نگاشت
         افعال وجهی که بند ۱۳٫۲ استاندارد آن را در هر سند یکسان می‌خواهد.
      ج) سطر عنوان بند — عنوان یک بند در فهرست مطالب و متن تکرار می‌شود.
    """
    glyph = re.compile(
        r"^[\u250C\u2510\u2514\u2518\u251C\u2524\u252C\u2534\u253C\u2502\u2500\u2501\u2551\u2554\u2557\u255A\u255D\u2560\u2563\u2566\u2569\u256C\u2570_=+*#~]{3,}$"
    )
    citation = re.compile(r"STD-HYD-(?:WRITE|VOICE)-v\d")
    seen: dict[str, int] = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if len(stripped) < minimum or "\t" in stripped:
            continue
        if glyph.match(stripped) or citation.search(stripped):
            continue
        seen[stripped] = seen.get(stripped, 0) + 1
    return [
        f"\u00d7{count}  \u00ab{line[:60]}\u00bb"
        for line, count in sorted(seen.items(), key=lambda x: -x[1])
        if count > 2
    ]


def load_register_ids() -> set[str] | None:
    """شناسه‌های موجود در رجیستر مرجع، یا None اگر رجیستر خوانده نشد.

    None عمداً با مجموعهٔ خالی فرق دارد: مجموعهٔ خالی یعنی رجیستر خالی است،
    و None یعنی رجیستر اصلاً خوانده نشد. بررسی وجود شناسه در حالت None
    نباید خاموشانه بی‌اثر شود، چون آن‌وقت دروازه وانمود می‌کند کار می‌کند
    در حالی که بررسی وجود اصلاً اجرا نشده است.
    """
    path = os.path.join(ROOT, "_مرجع", "HDR.csv")
    if not os.path.exists(path):
        print(f"⛔ رجیستر یافت نشد: {path}", file=sys.stderr)
        return None
    with open(path, encoding="utf-8") as handle:
        return {row["id"].strip() for row in csv.DictReader(handle)}


def check_id_column(text: str, known: set[str] | None) -> list[dict]:
    """قاعدهٔ ساختاری: ستون شناسهٔ پیوست الف باید شناسهٔ معتبر و موجود داشته باشد.

    سه شرط، به‌ترتیب:
      ۱. ستون از سرستون پیدا می‌شود، نه از موقعیت ثابت — قالب جدول یکسان نیست
         و بعضی کتابچه‌ها ستون «نوع مبنا» دارند و پس از شناسه می‌آید.
      ۲. مقدار باید الگوی شناسهٔ رجیستر را داشته باشد — این رشته‌های متنی را
         می‌گیرد، از جمله هر بن‌بستی که کارگر تازه بسازد.
      ۳. شناسه باید واقعاً در HDR.csv وجود داشته باشد — این شناسه‌های
         پُرظاهرِ ساختگی را می‌گیرد.

    اگر رجیستر خوانده نشده باشد، شرط سوم با خطای صریح گزارش می‌شود و
    بازبینی در حالت نامعتبر می‌ماند، نه اینکه بی‌سروصدا بگذرد.
    """
    bad: list[dict] = []
    in_appendix = False
    id_index = -1
    for number, line in enumerate(text.split("\n"), start=1):
        if "پیوست الف — ردیابی داده" in line:
            in_appendix = True
        if in_appendix and "راهنمای اجرایی کشاورز" in line:
            in_appendix = False
        # هر برچسب جدول یا شکل، مرز جدید است و باید نشانگر ستون را باطل کند.
        # پیوست الف چند جدول با سرستون‌های متفاوت دارد؛ بدون این بازنشانی،
        # نشانگر روی شمارهٔ ستون گیر می‌کند و ستون‌هایی مثل «مقدار دوم» یا
        # «وضعیت آن فصل» به‌جای ستون شناسه بازرسی می‌شوند.
        # شمارهٔ جدول می‌تواند حرفی هم باشد — «جدول الف.۲» — و سطر برچسب
        # معمولاً تب ندارد، پس این بازنشانی باید پیش از نگهبانِ تب بیاید.
        if re.match(r"^\s*(?:جدول|شکل)\s+[۰-۹\w]+", line):
            id_index = -1
            continue
        if not in_appendix or "\t" not in line:
            continue

        cells = [c.strip() for c in line.split("\t")]
        if cells and cells[0] == "شاخص":
            id_index = next((i for i, c in enumerate(cells) if c.startswith("شناسه")), -1)
            continue
        if id_index < 0 or len(cells) <= id_index:
            continue

        indicator, ident = cells[0], cells[id_index]
        if not indicator or SELF_ROW.search(indicator) or not ident:
            continue
        # فقط ردیفی بررسی می‌شود که ستون مقدارِ آن کمّی باشد. جدول مغایرت
        # ستون «بند بسته‌کننده» دارد که متن است نه مقدار؛ بدون این شرط، دروازه
        # متن آن ستون را شناسه می‌خواند و ده سیگنال کاذب می‌سازد.
        value_cell = cells[1] if len(cells) > 1 else ""
        if not re.search(r"[۰-۹0-9]", value_cell):
            continue
        if ident in APPROVED_ID_VALUES:
            continue
        # ردیف مغایرت، کمّیت نیست بلکه گزارش اختلاف است؛ جای آن متن است نه
        # شناسه. هر دو نشانه با هم بیاید، وگرنه یکی از آن‌ها به‌تنهایی درِ فرار
        # می‌شود: کافی بود شاخص با واژهٔ «مغایرت» آغاز شود تا هر متنی
        # در ستون شناسه پذیرفته شود.
        if indicator.startswith("مغایرت") and ident.startswith(CONTRA_MARK):
            continue
        if ID_PATTERN.match(ident):
            if known is None:
                bad.append(
                    {
                        "line": number,
                        "indicator": indicator[:60],
                        "value": ident[:60],
                        "reason": "رجیستر خوانده نشد — بررسی وجود اجرا نشد",
                    }
                )
            elif ident in known:
                continue
            else:
                bad.append(
                    {
                        "line": number,
                        "indicator": indicator[:60],
                        "value": ident[:60],
                        "reason": "شناسه در رجیستر نیست",
                    }
                )
            continue
        bad.append(
            {
                "line": number,
                "indicator": indicator[:60],
                "value": ident[:60],
                "reason": "الگو نامعتبر",
            }
        )
    return bad


FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


# سرفصل فصل ممکن است با پیشوند Markdown نوشته شده باشد؛ هر دو قالب را می‌پذیرد
# و گزارش می‌دهد کدام کتابچه‌ها قالب ناسازگار دارند.
_CHAPTER_STRICT = re.compile(r"^فصل\s+([۰-۹]+)\s+—")
# پیشوند Markdown اختیاری است؛ اگر با #{1,6} نوشته شود حداقل یک # لازم می‌شود
# و سرفصل‌های قالب‌ساده دیگر دیده نمی‌شوند.
_CHAPTER_LOOSE = re.compile(r"^(?:#{1,6}\s*)?فصل\s+([۰-۹]+)\s+—")
_FA = "۰۱۲۳۴۵۶۷۸۹"
_MAP = str.maketrans(_FA, "0123456789")


def _count_headings(lines: list[str]) -> int:
    """شمار سرفصل فصل — فقط سطر مستقل، نه سطر جدول."""
    seen: set[int] = set()
    for line in lines:
        m = _CH_LOOSE.match(line)
        if m:
            seen.add(int(m.group(1).translate(_MAP)))
    return len(seen)


def chapter_sizes(lines: list[str]) -> dict[int, int]:
    """اندازهٔ هر فصل را از شمارهٔ سطر شروع آن تا شروع فصل بعد حساب می‌کند.

    نکتهٔ مهم: هر شمارهٔ فصل ممکن است بیش از یک‌بار بیاید — یک‌بار سرفصل واقعی
    و بار دوم در فهرست جدول‌های ضمائم که با همان قالب نوشته شده است. اگر
    occurrence دوم جای اول را بگیرد، اندازهٔ فصل از سطری که فهرست ضمائم شروع
    می‌شود محاسبه می‌شود و کف عملاً صفر نشان داده می‌شود. پس **اولین** occurrence
    ملاک است، نه آخری.
    """
    first: dict[int, int] = {}
    for i, line in enumerate(lines):
        m = _CH_LOOSE.match(line)
        if not m:
            continue
        number = int(m.group(1).translate(_MAP))
        if number in CHAPTER_FLOORS and number not in first:
            first[number] = i + 1

    # شروع فصل بعد، حتی اگر شماره‌اش تکراری باشد
    order: list[tuple[int, int]] = sorted((start, number) for number, start in first.items())
    sizes: dict[int, int] = {}
    for index, (start, number) in enumerate(order):
        end = order[index + 1][0] if index + 1 < len(order) else len(lines) + 1
        sizes[number] = end - start
    return sizes


def markdown_headings(lines: list[str]) -> int:
    """شمار سرفصل‌های فصل که پیشوند Markdown دارند و با قالب مجموعه ناسازگارند."""
    return sum(
        1 for line in lines if _CHAPTER_LOOSE.match(line) and not _CHAPTER_STRICT.match(line)
    )


def gate_hits(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name, (lo, hi) in GATE_RANGES.items():
        n = sum(1 for ch in text if lo <= ord(ch) <= hi)
        if n:
            counts[name] = n
    return counts


def classify(phrase: str, line: str) -> str:
    """یک خط حاوی عبارت ممنوعه را در سه طبقهٔ نقض، فنی-محدود و نفی-ممنوعی می‌گذارد."""
    if any(m in line for m in NEGATION_MARKERS):
        return "نفی-ممنوعی"
    if phrase in ("تنها راه", "تنها راهکار") and any(m in line for m in BOUNDED_MARKERS):
        return "فنی-محدود"
    return "نقض"


def scan_claims(text: str) -> dict[str, list[dict]]:
    """همهٔ عبارت‌های ممنوعه را با طبقه و محل برمی‌گرداند."""
    found: dict[str, list[dict]] = {}
    for number, line in enumerate(text.split("\n"), start=1):
        for phrase in BANNED_CLAIMS:
            if phrase not in line:
                continue
            found.setdefault(phrase, []).append(
                {"line": number, "class": classify(phrase, line), "text": line.strip()[:150]}
            )
    return found


def audit(path: str, known: set[str] | None) -> dict:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    lines = text.split("\n")
    sizes = chapter_sizes(lines)
    claims = scan_claims(text)
    violations = [
        {**hit, "phrase": phrase}
        for phrase, hits in claims.items()
        for hit in hits
        if hit["class"] == "نقض"
    ]
    forbidden = {name: text.count(name) for name in FORBIDDEN_STRINGS if text.count(name)}
    return {
        "file": os.path.basename(path),
        "lines": len(lines),
        "line_ok": len(lines) >= LINE_FLOOR,
        "chapters": _count_headings(lines),
        "chapter_ok": len(sizes) == 12,
        "markdown_headings": markdown_headings(lines),
        "chapter_sizes": sizes,
        "floors_met": sorted(k for k, v in sizes.items() if v >= CHAPTER_FLOORS[k]),
        "floors_short": {
            k: CHAPTER_FLOORS[k] - v for k, v in sorted(sizes.items()) if v < CHAPTER_FLOORS[k]
        },
        "appendix_a": "پیوست الف — ردیابی داده" in text,
        "farmer_guide": "راهنمای اجرایی کشاورز" in text,
        "closing_line": "پایان بستهٔ مهندسی" in text,
        "gate": gate_hits(text),
        "gate_ok": not gate_hits(text),
        "violations": violations,
        "claims_ok": not violations,
        "forbidden": forbidden,
        "forbidden_ok": not forbidden,
        "bad_id_cells": check_id_column(text, known),
        "census": table_census(text),
        "census_drift": census_drift(path, table_census(text)),
        "duplicate_lines": duplicate_lines(text),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="خروجی ساختاریافته")
    args = parser.parse_args()

    if not os.path.isdir(ROOT):
        print(f"پوشه پیدا نشد: {ROOT}", file=sys.stderr)
        return 2

    # دامنهٔ ممیزی فقط کتابچه‌ها نبود. تا ساعتی که این خط این‌طور بود، هفت جلد
    # تحویل از دروازهٔ نویسه، دروازهٔ بن‌بست و دروازهٔ صداقت بیرون ماندند و هیچ
    # ممیزی دربارهٔ آن‌ها اجرا نشد.
    files = sorted(
        f
        for f in os.listdir(ROOT)
        if f.endswith((".txt", ".md")) and not f.startswith("_") and f != "سیاهه-نقل-بین‌المللی.md"
    )
    known = load_register_ids()
    results = [audit(os.path.join(ROOT, f), known) for f in files]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    total = sum(r["lines"] for r in results)
    complete = sum(1 for r in results if r["line_ok"] and r["chapter_ok"])
    gate_fail = [r["file"] for r in results if not r["gate_ok"]]
    violations_total = [{**hit, "file": r["file"]} for r in results for hit in r["violations"]]
    forbidden_total = {
        name: sum(r["forbidden"].get(name, 0) for r in results) for name in FORBIDDEN_STRINGS
    }
    forbidden_total = {k: v for k, v in forbidden_total.items() if v}
    reject_count = sum(
        1 for r in results if not r["forbidden_ok"] or not r["claims_ok"] or not r["gate_ok"]
    )

    print(f"پوشه: {ROOT}")
    print(f"کتابچه: {len(results)}  ·  جمع سطر: {total:,}  ·  رسیده به {LINE_FLOOR}: {complete}")
    print(f"استاندارد STD-HYD-WRITE-v1.0 — کتابچه‌های ردشده: {reject_count}")
    print()
    header = (
        f"{'فایل':<30}{'سطر':>7}{'فصل':>5}{'ضمیمه':>7}{'راهنما':>7}{'کف‌ها':>6}"
        f"{'نقض':>6}{'بن‌بست':>8}  دروازه"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        dead = sum(r["forbidden"].values())
        print(
            f"{r['file']:<30}{r['lines']:>7}{r['chapters']:>5}"
            f"{'بله' if r['appendix_a'] else '—':>7}{'بله' if r['farmer_guide'] else '—':>7}"
            f"{len(r['floors_met']):>6}{len(r['violations']):>6}{dead:>8}  "
            f"{'سالم' if r['gate_ok'] else '⚠ ' + str(r['gate'])}"
        )

    short = [(r["file"], sum(r["floors_short"].values())) for r in results if r["floors_short"]]
    if short:
        print("\nفصل‌های زیر کف سطری:")
        for name, gap in sorted(short, key=lambda x: -x[1]):
            print(f"  {name:<30} کسر {gap} سطر")

    if gate_fail:
        print(f"\n⚠ دروازهٔ کنترل کاراکتر: {len(gate_fail)} فایل — {' · '.join(gate_fail)}")
    else:
        print("\nدروازهٔ کنترل کاراکتر: صفر مورد در همهٔ فایل‌ها")

    if violations_total:
        print(f"\n⚠ نقض بند ۷ — {len(violations_total)} مورد (ادعای زنده بدون معیار):")
        for hit in violations_total:
            print(f"  {hit['file']} L{hit['line']} [{hit['phrase']}]: {hit['text']}")
    else:
        print("نقض بند ۷: صفر مورد — هر عبارت در بافت نفی، گزارش حذف یا کاربرد فنی محدود است")

    if forbidden_total:
        print(
            f"\n⛔ بن‌بست — {sum(forbidden_total.values()):,} مورد (STD-HYD-WRITE-v1.0 بند ۲٫۵):".replace(
                ",", "٬"
            )
        )
        for name, n in sorted(forbidden_total.items(), key=lambda x: -x[1]):
            print(f"  {name}: {n:,} — {FORBIDDEN_STRINGS[name]}".replace(",", "٬"))
        for r in results:
            if r["forbidden"]:
                parts = " · ".join(f"{k}={v}" for k, v in sorted(r["forbidden"].items()))
                print(f"    {r['file']}: {parts}")
    else:
        print("بن‌بست: صفر مورد — هیچ رشتهٔ ممنوعه در مجموعه نیست")

    bad_cells = [(r["file"], c) for r in results for c in r["bad_id_cells"]]
    if bad_cells:
        by_file: dict[str, int] = defaultdict(int)
        for name, _ in bad_cells:
            by_file[name] += 1
        print(
            f"\n⛔ سلول شناسهٔ نامعتبر — {len(bad_cells):,} مورد (قاعدهٔ ساختاری):".replace(",", "٬")
        )
        for name, n in sorted(by_file.items(), key=lambda x: -x[1]):
            print(f"  {n:>5}  {name}")
        print("  نمونه:")
        for name, cell in bad_cells[:6]:
            print(f"    {name} L{cell['line']} — «{cell['value']}»")
    else:
        print("ستون شناسهٔ پیوست الف: هر ردیف یا شناسهٔ معتبر دارد یا در فهرست ردیف‌های مجاز است")

    dupes = [(r["file"], d) for r in results for d in r["duplicate_lines"]]
    if dupes:
        print(f"\n⚠ سطر تکراریِ بلند — {len(dupes)} مورد (پُرشدگی، بند ۶٫۱ ممنوع):")
        for name, d in dupes[:12]:
            print(f"  {name}: {d}")

    drift = [(r["file"], d) for r in results for d in r["census_drift"]]
    if drift:
        print(f"\n⛔ افت یا حذف جدول نسبت به خط پایه — {len(drift)} مورد:")
        for name, d in drift[:20]:
            print(f"  {name}: {d}")
    else:
        print("شمار سطر جدول‌ها نسبت به خط پایه: بدون افت و بدون حذف")

    return 1 if reject_count or bad_cells else 0


if __name__ == "__main__":
    raise SystemExit(main())
