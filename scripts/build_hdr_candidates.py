"""موج صفر — ساخت ردیف‌های تازهٔ رجیستر HDR.csv.

از پیوست الف هر ۲۳ کتابچه، ردیف‌هایی را که ستون شناسهٔ آن‌ها «فاقد شناسه» است
استخراج می‌کند و برای هر ردیف یک ردیف رجیستر با شناسهٔ یکتا می‌سازد.

خروجی دو فایل است:
  - scripts/hdr_candidates.csv    ردیف‌های پیشنهادی برای بازبینی و درج
  - scripts/hdr_candidates.md     گزارش خوانا برای بازبینی

این ابزار خودش در HDR.csv نمی‌نویسد. نوشتن بر عهدهٔ بازبین انسانی است.

اجرا:  python scripts/build_hdr_candidates.py
"""

from __future__ import annotations

import csv
import glob
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BOOKS = os.path.join(ROOT, "کتابها")
REGISTER = os.path.join(BOOKS, "_مرجع", "HDR.csv")
OUT_CSV = os.path.join(HERE, "hdr_candidates.csv")
OUT_MD = os.path.join(HERE, "hdr_candidates.md")

FIELDS = [
    "id",
    "domain",
    "indicator",
    "value",
    "unit",
    "source_primary",
    "year",
    "confidence",
    "consumers",
    "action",
    "status",
]

# خانوادهٔ شناسه بر پایهٔ حوزهٔ موضوعی، از استاندارد نگارش بند ۱٫۳
DOMAIN_FAMILY = {
    "هویت": ("ID", "هویت و تاریخ"),
    "مقیاس": ("SC", "مقیاس"),
    "مالی": ("FN", "مالی"),
    "خدمات اکوسیستمی": ("ES", "خدمات اکوسیستمی"),
    "کربن": ("CB", "کربن"),
    "هدف فنی": ("TO", "هدف فنی"),
    "استاندارد": ("ST", "استاندارد"),
    "مدل شبیه‌سازی": ("MD", "مدل شبیه‌سازی"),
    "پایلوت": ("PL", "پایلوت"),
    "آمار ملی": ("NS", "آمار ملی"),
    "پایش": ("MR", "پایش"),
    "بسته فنی": ("HP", "بستهٔ فنی"),
    "حکمرانی": ("GV", "حکمرانی"),
    "محیط زیست": ("S", "محیط زیست"),
    "دسترسی": ("AT", "دسترسی نهادی"),
    "اقلیم": ("CL", "اقلیم"),
    "قیمت": ("PR", "قیمت"),
    "مواد": ("M", "ماده"),
    "گونه": ("SP", "گونه"),
    "تجهیزات": ("EM", "تجهیزات"),
    "ریسک": ("R", "ریسک"),
    "مدیریت": ("ID", "هویت و مدیریت"),
}

# نشانه‌هایی که مقدار را «انتخاب‌شده» از «محاسبه‌شده» جدا می‌کند
DECISION_MARKERS = ("نرخ", "انتخاب", "تصمیم", "مبنای", "ضریب اطمینان", "کف ", "سقف ")
DERIVED_MARKERS = ("×", "÷", "=", "محاسبه", "بازمحاسبه", "مشتق")

PACKAGE = re.compile(r"^HP-(\d+)")


def read_register() -> tuple[set[str], list[dict]]:
    with open(REGISTER, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {r["id"].strip() for r in rows}, rows


HEADERS = ("شاخص", "مقدار", "واحد", "شناسه HDR", "سطح اطمینان")
# ستون‌هایی که در پیوست الف تکرار می‌شوند و ردیف رجیستر نمی‌سازند
SELF_DECLARED = re.compile(
    r"تعداد (شکل|جدول|فرمول)|بازهٔ زمانی|شروع رسمی طرح|نرخ ارز مرجع|تعداد ردیف|مجموع|جمع "
)
# ردیفی که مقدارش عدد است یک کمّیت واقعی است؛ متن، کد و عنوان، کمّیت نیستند
QUANTITY = re.compile(r"[۰-۹0-9]")


def appendix_rows(text: str) -> list[list[str]]:
    """ردیف‌های جدول پیوست الف را با هم‌ترازی درست ستون‌ها برمی‌گرداند.

    فهرست مطالب هم عنوان «پیوست الف — ردیابی داده» را دارد، پس باید
    دنبال آخرین عنوانی بگردیم که بلافاصله پس از آن سرستون جدول آمده است.
    """
    lines = text.split("\n")

    def is_header(line: str) -> bool:
        cells = [c.strip() for c in line.split("\t") if c.strip()]
        return len(cells) == 5 and tuple(cells) == HEADERS

    start = None
    for i, line in enumerate(lines):
        if not is_header(line):
            continue
        # سرستون باید پس از عنوان پیوست الف آمده باشد
        window = "\n".join(lines[max(0, i - 20) : i])
        if "پیوست الف" in window:
            start = i
    if start is None:
        return []

    out: list[list[str]] = []
    for line in lines[start + 1 :]:
        if "راهنمای اجرایی کشاورز" in line and out:
            break
        if "\t" not in line:
            continue
        cells = [c.strip() for c in line.split("\t")]
        # سلول‌های خالی میانی را نگه می‌داریم تا ستون‌ها جابه‌جا نشوند
        while len(cells) < 5:
            cells.append("")
        cells = cells[:5]
        if not cells[0] or not QUANTITY.search(cells[1]):
            continue
        if SELF_DECLARED.search(cells[0]):
            continue
        out.append(cells)
    return out


def pick(cells: list[str], index: int, default: str = "") -> str:
    return cells[index] if len(cells) > index else default


def classify_source(indicator: str, value: str, unit: str) -> tuple[str, str]:
    """نوع مبنا و کنش لازم را برمی‌گرداند.

    خروجی یک جفت است: پایهٔ متن source و پیشوند action.
    لنگرگاه بند بعداً به متن source افزوده می‌شود.
    """
    text = f"{indicator} {value} {unit}"
    if any(m in text for m in DECISION_MARKERS):
        return "تصمیم طراحی", "تثبیت مبنای تصمیم و بازبینی در فاز کالیبراسیون"
    if any(m in text for m in DERIVED_MARKERS):
        return "محاسبهٔ فرض طراحی", "تکرار محاسبه در فاز کالیبراسیون"
    return "فرض طراحی", "تعیین مبنای عدد و بازبینی در فاز کالیبراسیون"


def guess_domain(indicator: str, unit: str) -> tuple[str, str]:
    text = f"{indicator} {unit}"
    if re.search(r"قیمت|هزینه|دلار|سرمایه|بازگشت|نسبت B", text):
        return "مالی", "مالی"
    if re.search(r"مساحت|هکتار|مقیاس|سطح S", text):
        return "مقیاس", "مقیاس"
    if re.search(r"خدمات اکوسیستمی|ES|گرده|کربن|آبخوان|سیلاب|حاصلخیزی", text):
        return "خدمات اکوسیستمی", "خدمات اکوسیستمی"
    if re.search(r"استاندارد|ISO|ISO\)|آزمون", text):
        return "استاندارد", "استاندارد"
    if re.search(r"مدل|RUSLE|WEPP|SWAT|شبیه", text):
        return "مدل شبیه‌سازی", "مدل شبیه‌سازی"
    if re.search(r"پایلوت|PL-0", text):
        return "پایلوت", "پایلوت"
    if re.search(r"گونه|بذر|گیاه|درخت|بوته", text):
        return "گونه", "گونه"
    if re.search(r"سنگ|چوب|لوله|حوضچه|اسپریکلر|خاک|مالچ|مواد|ماده", text):
        return "مواد", "ماده"
    if re.search(r"آبشخور|تجهیز|حسگر|شیر|ابزار", text):
        return "تجهیزات", "تجهیزات"
    if re.search(r"ریسک|خطر|خرابی|احتمال|شدت", text):
        return "ریسک", "ریسک"
    if re.search(r"سهم|کارگروه|کمیته|حکمرانی|وتو", text):
        return "حکمرانی", "حکمرانی"
    if re.search(r"زیست‌محیط|محیط زیست|تنوع گیاهی|H′", text):
        return "محیط زیست", "محیط زیست"
    return "هدف فنی", "هدف فنی"


CLAUSE = re.compile(r"(?:بند|جدول|شکل|فرمول)\s+([\u06F0-\u06F9\d]+[\u066B\u066C.\u06F0-\u06F9\d]*)")


def anchor_clause(text: str, indicator: str) -> str:
    """نزدیک‌ترین ارجاع بند یا جدول پیش از نخستین occurrence شاخص را برمی‌گرداند.

    این کار ستون source_primary را از یک عبارت کلی به یک لنگرگاه مشخص
    تبدیل می‌کند تا ردیف رجیستر واقعاً قابل بازبینی باشد.
    """
    # واژهٔ شاخص را به یک عبارت جست‌وجوی معنادار کوتاه می‌کنیم
    core = re.sub(r"[（）()\[\]].*", "", indicator).split("—")[0].strip()
    words = [w for w in re.findall(r"[\u0600-\u06FF]{3,}", core) if len(w) > 3]
    if not words:
        return ""
    needle = max(words, key=len)

    lines = text.split("\n")
    positions = [i for i, line in enumerate(lines) if needle in line]
    if not positions:
        positions = [i for i, line in enumerate(lines) if words[0] in line]
    if not positions:
        return ""

    last_seen: str = ""
    for i in range(positions[0] + 1):
        found = CLAUSE.search(lines[i])
        if found:
            last_seen = found.group(1)
    return last_seen


def main() -> int:
    if not os.path.isdir(BOOKS):
        print(f"پوشه پیدا نشد: {BOOKS}", file=sys.stderr)
        return 2

    taken, _ = read_register()
    candidates: list[dict] = []
    per_book: dict[str, int] = {}

    for path in sorted(glob.glob(os.path.join(BOOKS, "HP-*.txt"))):
        name = os.path.basename(path)
        match = PACKAGE.match(name)
        if not match:
            continue
        code = f"HP-{match.group(1)}"
        with open(path, encoding="utf-8") as _fh:
            text = _fh.read()

        count = 0
        for cells in appendix_rows(text):
            indicator = cells[0]
            value = pick(cells, 1)
            unit = pick(cells, 2)
            idcol = pick(cells, 3)
            conf = pick(cells, 4, "C")

            if "فاقد شناسه" not in idcol:
                continue
            if not value or not indicator:
                continue
            # ردیف‌های خوداظهاری و ثابت، شناسهٔ ثابت دارند و تکراری‌اند
            if re.search(
                r"تعداد (شکل|جدول|فرمول)|بازهٔ زمانی اعداد|شروع رسمی طرح|نرخ ارز مرجع|تعداد ردیف",
                indicator,
            ):
                continue
            if len(indicator) < 3:
                continue

            domain, registry_domain = guess_domain(indicator, unit)
            family, _ = DOMAIN_FAMILY.get(domain, ("TO", "هدف فنی"))

            clause = anchor_clause(text, indicator)
            kind, action = classify_source(indicator, value, unit)
            if clause:
                source = f"{kind} — بند {clause}"
            else:
                source = f"{kind} — بی‌لنگرگاه: باید در بند متناظر کتابچه لنگر شود"
                action = "تعیین بند متناظر و نوشتن مبنای عدد در همان بند"

            candidates.append(
                {
                    "id": "",  # در گام بعد ساخته می‌شود
                    "domain": registry_domain,
                    "indicator": indicator,
                    "value": value,
                    "unit": unit,
                    "source_primary": source,
                    "year": "۱۴۰۵",
                    "confidence": (conf[0] if conf[:1] in "ABC" else "C"),
                    "consumers": code,
                    "action": action,
                    "status": "ثبت شد",
                    "_family": family,
                    "_clause": clause,
                }
            )
            count += 1
        per_book[code] = count

    # یکتایی شاخص: همان شاخص در چند بسته، یک شناسهٔ یکتا می‌گیرد
    seen_indicator: dict[str, set[str]] = defaultdict(set)
    for row in candidates:
        seen_indicator[row["indicator"]].add(row["consumers"])
    for row in candidates:
        packages = seen_indicator[row["indicator"]]
        if len(packages) > 1:
            row["indicator"] = f"{row['indicator']} — {row['consumers']}"

    # شناسهٔ یکتا می‌سازیم و از شناسه‌های موجود رجیستر پرهیز می‌کنیم
    counters: dict[str, int] = defaultdict(int)
    used: set[str] = set()
    for row in candidates:
        family = row.pop("_family")
        while True:
            counters[family] += 1
            new_id = f"{family}-{counters[family]:02d}"
            if new_id not in taken and new_id not in used:
                break
        row["id"] = new_id
        used.add(new_id)

    anchored = sum(1 for r in candidates if r.pop("_clause", ""))
    unanchored = len(candidates) - anchored

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in candidates:
            writer.writerow({k: row[k] for k in FIELDS})

    with open(OUT_MD, "w", encoding="utf-8") as handle:
        handle.write("# ردیف‌های پیشنهادی رجیستر — بازبینی پیش از درج\n\n")
        handle.write(f"تعداد کل: **{len(candidates)}** ردیف تازه\n\n")
        handle.write("## تفکیک بر پایهٔ بسته\n\n")
        for code, n in sorted(per_book.items(), key=lambda x: -x[1]):
            handle.write(f"- `{code}`: {n} ردیف\n")
        handle.write("\n## تفکیک بر پایهٔ حوزه\n\n")
        for domain, n in Counter(r["domain"] for r in candidates).most_common():
            handle.write(f"- {domain}: {n} ردیف\n")
        handle.write("\n## تفکیک بر پایهٔ سطح اطمینان\n\n")
        for level, n in Counter(r["confidence"] for r in candidates).most_common():
            handle.write(f"- سطح {level}: {n} ردیف\n")
        handle.write("\n## نکته‌های بازبینی\n\n")
        write = handle.write
        write(f"- ردیف‌های لنگرگاه‌دار: {anchored} · بی‌لنگرگاه: {unanchored}\n")
        write("- ردیف بی‌لنگرگاه نباید در رجیستر درج شود تا وقتی بند متناظرش تعیین گردد.\n")
        write("- هر ردیف باید پیش از درج، در بند متناظر کتابچه دیده شود.\n")
        write(
            "- ردیف‌هایی که مقدارشان در کتابچه محاسبه نشده، باید یا محاسبه شوند یا از رجیستر حذف شوند.\n"
        )
        write("- ستون `action` پیشنهادی است و باید با وضعیت واقعی هر بسته تطبیق داده شود.\n")

    print(f"ردیف‌های پیشنهادی: {len(candidates)}")
    print(f"لنگرگاه‌دار: {anchored}  ·  بی‌لنگرگاه: {unanchored}")
    print(f"نوشته شد:\n  {OUT_CSV}\n  {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
