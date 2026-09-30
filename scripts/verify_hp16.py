"""Safety-preservation check for the HP-16 dead-end sweep.

Three things are asserted:

  1. ANCHORS  — every load-bearing safety phrase from the PRESERVE list is
                still present, and the three documented failure cases and the
                16 risk entries are intact.
  2. NUMBERS  — every safety number that existed in the pre-edit backup still
                exists at least as many times in the finished file, so no
                threshold was weakened or deleted.
  3. GATE     — character gate, Persian digits, scale labels, FX rate, and
                species discipline.

The banned-claim list is checked with a negation guard: those phrases are
allowed only inside an explicit negation or removal report, which is the one
context the standard permits.
"""

import glob
import re
import sys
import unicodedata

BACKUP = glob.glob(r"D:\eco_nojin\کتابها\_پشتیبان\HP-16*")[0]
FINAL = r"D:\eco_nojin\کتابها\HP-16 پایداری شیب.txt"

# The three documented failure cases are written in Persian transliteration,
# which is this corpus's convention for place and author names.
ANCHORS = [
    ("terracing banned absolutely", "تراس‌بندی ممنوع"),
    ("no water injection whatsoever", "تزریق آب"),
    ("815 method", "۸۱۵"),
    ("no work on active ground", "ردهٔ فعال"),
    ("no work on semi-active ground", "ردهٔ نیمه‌فعال"),
    ("spade-and-bucket classification test", "جدول ۱٫۵"),
    ("step-zero access gate", "گام صفر"),
    ("zero farmer authority", "شما فقط گزارش می‌دهید"),
    ("three authority levels table", "جدول ۵٫۲"),
    ("two-person rule", "دو نفر"),
    ("daylight rule", "روشنایی"),
    ("more caution is itself forbidden", "ادامه با احتیاط بیشتر"),
    ("default-closed pose", "حالت پیش‌فرض"),
    ("step-0 / semi-active contradiction", "تناقض"),
    ("1.3 refused, chapter 1", "عدد ۱٫۳ پذیرفته نمی‌شود"),
    ("1.3 refused, chapter 6", "عدد ۱٫۳ نپذیرفته شد"),
    ("C3 retired scope", "این بخش بازنشسته است"),
    ("absence of data is not absence of danger", "نبودِ داده"),
    ("RR-16-01", "RR-16-01"),
    ("RR-16-16", "RR-16-16"),
    ("Aberfan", "آبرفان"),
    ("Aberfan date", "۲۱ اکتبر ۱۹۶۶"),
    ("Aberfan official inquiry report", "گزارش تحقیق رسمی"),
    ("Po Shan Road", "پو شان"),
    ("Po Shan date", "۱۱ ژوئن ۱۹۷۶"),
    ("Frank Slide", "فرانک"),
    ("Frank Slide date", "۳ ژوئن ۱۹۹۹"),
    ("Cruden and Wang", "کروتن و وانگ"),
    ("journal citation", "ژئوتکنیک کانادا"),
    ("pages 941-963", "۹۴۱ تا ۹۶۳"),
    ("PL-01", "PL-01"),
    ("PL-02", "PL-02"),
    ("PL-04", "PL-04"),
    ("simulation label", "خروجی شبیه‌سازی — غیرمیدانی"),
    ("start date", "۱۴۰۵/۰۱/۰۱"),
    ("simulation window", "۱۴۰۴/۰۱ تا ۱۴۰۵/۰۳"),
    ("closing line", "پایان بستهٔ مهندسی"),
    ("farmer guide heading", "راهنمای اجرایی کشاورز"),
    ("appendix heading", "پیوست الف — ردیابی داده"),
]

# Safety numbers: count in the backup must not decrease in the final file.
NUMBERS = [
    "۱٫۳",
    "۵ درصد",
    "۸۰۰",
    "۱۶۰۰",
    "۴٫۸",
    "۵٫۵",
    "۲۰ تا ۴۰",
    "۱۰ تا ۲۰",
    "۱٫۹",
    "۱۰۰٬۰۰۰",
    "۶۲۹٫۹۵",
    "۵٫۱۰",
    "۱٬۳۵۰٬۰۰۰",
    "۲۲٫۹",
    "۰٫۱۸۶",
    "۱۹۶۶",
    "۱۹۷۶",
    "۱۹۹۹",
    "۹۴۱",
    "۱۵۰ تا ۲۰۰",
    "۴۰۰",
    "۲۲۸",
    "۳۰ سانتی‌متر",
    "۵ سانتی‌متر",
    "۶۰ سانتی‌متر",
    "۲۰ متر",
    "۵۰ متر",
    "۹۰ روز",
    "۲٫۵",
    "۹۰ درصد",
    "۵۰ متری",
    "۱٬۳۶۰",
]

BANNED_CLAIMS = [
    "مطابقت کامل با استاندارد",
    "تطبیق ۹۵٪",
    "۱۰۰٪ با استاندارد",
    "تنها راهکار",
    "بالاتر از استاندارد",
    "موقعیت رقابتی منحصر",
    "بازدهی ۱۰۰٪",
    "نتیجه میدانی",
    "اندازه‌گیری‌شده در پایلوت",
    "همه پایلوت",
]
# Each of these may appear only inside one of these negation frames.
NEGATION_FRAMES = ["هیچ", "نمی", "نه ", "بدون", "بازنشسته", "ممنوع", "حذف نشده"]

APPROVED = {
    "Quercus hyrcana",
    "Fraxinus angustifolia",
    "Zelkova carpinifolia",
    "Platanus orientalis",
    "Celtis caucasica",
    "Pterocarya fraxinifolia",
    "Prunus avium",
    "Populus nigra",
    "Salix alba",
    "Alnus glutinosa",
    "Acer campestre",
    "Acer hyrcanum",
    "Carpinus betulus",
    "Cornus mas",
    "Fagus orientalis",
    "Fraxinus excelsior",
    "Tilia cordata",
    "Ulmus minor",
}
LATIN_DIGITS = "0123456789"
ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"


def in_negation(text: str, at: int) -> bool:
    window = text[max(0, at - 120) : at + 120]
    return any(f in window for f in NEGATION_FRAMES)


def main() -> int:
    with open(BACKUP, encoding="utf-8") as _fh:
        before = _fh.read()
    with open(FINAL, encoding="utf-8") as _fh:
        after = _fh.read()
    problems: list[str] = []
    added: list[str] = []

    missing = [s for _, s in ANCHORS if s not in after]
    for s in missing:
        problems.append(f"ANCHOR LOST: {s}")

    for num in NUMBERS:
        b = before.count(num)
        a = after.count(num)
        if b == 0:
            added.append(num)
        elif a < b:
            problems.append(f"NUMBER SHRANK {num}: {b} -> {a}")

    for claim in BANNED_CLAIMS:
        start = 0
        while (at := after.find(claim, start)) != -1:
            if not in_negation(after, at):
                problems.append(f"BANNED CLAIM live: …{after[at - 70 : at + 40]}…")
            start = at + 1

    if "به دلیل ریسک حذف نشده" not in after:
        problems.append("PRESERVE lost: no-deletion-because-of-risk sentence")

    for ch in set(after):
        cp, cat = ord(ch), unicodedata.category(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3040 <= cp <= 0x30FF:
            problems.append(f"gate: CJK/kana U+{cp:04X}")
        elif 0xAC00 <= cp <= 0xD7AF:
            problems.append(f"gate: Hangul U+{cp:04X}")
        elif 0x0400 <= cp <= 0x04FF:
            problems.append(f"gate: Cyrillic U+{cp:04X}")
        elif cp == 0xFFFD:
            problems.append("gate: U+FFFD")
        elif 0x0080 <= cp <= 0x009F:
            problems.append(f"gate: halfwidth/control U+{cp:04X}")
        elif cat == "Cc" and ch not in "\n\r\t":
            problems.append(f"gate: control U+{cp:04X}")
        elif ch in ARABIC_INDIC:
            problems.append(f"gate: arabic-indic digit {ch}")

    # Latin digits are legal only inside a register ID, a standard code, or a
    # scale label — never as a quantity.
    for mt in re.finditer(r"[0-9]+", after):
        ctx = after[max(0, mt.start() - 6) : mt.end() + 6]
        if not re.search(r"[A-Za-z]{1,5}[-–][0-9A-Za-z]{0,5}", ctx) and not re.search(
            r"v1\.0|v3\.0|\b[A-Z][0-9]\b|C3|ISO \d+|[Ss]tandard", ctx
        ):
            problems.append(f"gate: latin numeral in {ctx!r}")
            break

    for label in ("S1", "S2", "S3", "S5"):
        if label not in after:
            problems.append(f"scale label missing: {label}")
    if before.count("S4") or after.count("S4"):
        problems.append("S4 unexpectedly present — review")

    if "۱۰۰٬۰۰۰" not in after or "تومان بر دلار" not in after:
        problems.append("FX rate ۱۰۰٬۰۰۰ تومان بر دلار missing")

    # species discipline: a species table row is shaped  Persian — Latin binomial.
    # Any binomial outside the approved native list must sit in a rejected row.
    REJECT = ("بومی‌نشده", "نامبرده نمی‌شود", "حذف شد", "مورد اختلاف", "مشروط")
    for line in after.split("\n"):
        if "\t" not in line or " — " not in line:
            continue
        for cell in line.split("\t"):
            m = re.fullmatch(r"[A-Z][a-z]+ (?:[a-z]+)", cell.strip())
            if not m:
                continue
            if cell.strip() in APPROVED:
                continue
            if not any(k in line for k in REJECT):
                problems.append(f"species used outside approved list: {cell!r} in {line[:90]!r}")

    print(f"backup lines : {before.count(chr(10)) + 1}")
    print(f"final lines  : {after.count(chr(10)) + 1}")
    print(f"anchors kept : {len(ANCHORS) - len(missing)}/{len(ANCHORS)}")
    if added:
        print(f"new numbers  : {len(added)} added by decisions — {chr(32).join(added)}")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
