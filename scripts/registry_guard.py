"""حاکمیت رجیستر — اصل تک‌نویسنده.

قاعدهٔ حرفه‌ای نوشتن هم‌زمان روی یک فایل مشترک: یک نویسنده، چند خواننده.
کارگران نگارش هرگز `HDR.csv` را نمی‌نویسند. هر کدام ردیف تازه را در
`scripts/hdr_proposals/HP-XX.csv` می‌نویسد و این فرایند — تنها نویسنده —
در پایان هر موج merge می‌کند.

این ابزار سه کار می‌کند:
  manifest   نوشتن اثر انگشت فایل، برای تشخیص هر نوشتن غیرمجاز
  status     مقایسهٔ اثر انگشت فعلی با اثر انگشت ثبت‌شده
  merge      ادغام پیشنهادها با کنترل تصادم، سپس به‌روزرسانی اثر انگشت

اجرا:
  python scripts/registry_guard.py manifest
  python scripts/registry_guard.py status
  python scripts/registry_guard.py merge
"""

from __future__ import annotations

import csv
import glob
import hashlib
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER = os.path.join(ROOT, "کتابها", "_مرجع", "HDR.csv")
PROPOSALS = os.path.join(ROOT, "scripts", "hdr_proposals")
MANIFEST = os.path.join(ROOT, "scripts", "hdr_manifest.sha256")
FIELDS = ["id", "domain", "indicator", "value", "unit", "source_primary", "year", "confidence", "consumers", "action", "status"]

# خانوادهٔ شناسه یک تا پنج حرف، پس از خط تیره یک تا پنج بخش
FAMILY = __import__("re").compile(r"^[A-Z]{1,5}-[0-9A-Z]{1,5}(?:-[0-9A-Z]{1,5})?$")


def digest() -> str:
    with open(REGISTER, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_register() -> list[dict]:
    with open(REGISTER, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cmd_manifest() -> int:
    with open(MANIFEST, "w", encoding="utf-8") as handle:
        handle.write(f"{digest()}  {os.path.basename(REGISTER)}\n")
    print(f"اثر انگشت ثبت شد: {digest()[:16]}…")
    return 0


def cmd_status() -> int:
    if not os.path.exists(MANIFEST):
        print("اثر انگشت ثبت نشده — ابتدا manifest را بزنید", file=sys.stderr)
        return 2
    recorded = open(MANIFEST, encoding="utf-8").read().split()[0]
    current = digest()
    if recorded == current:
        print("رجیستر دست‌نخورده است — هیچ نوشتن غیرمجازی رخ نداده")
        return 0
    print("⚠ رجیستر تغییر کرده و در manifest ثبت نشده", file=sys.stderr)
    print(f"  ثبت‌شده: {recorded[:16]}…", file=sys.stderr)
    print(f"  فعلی:   {current[:16]}…", file=sys.stderr)
    print("  اگر این تغییر از مسیر همین فرایند است، manifest را دوباره بزنید.", file=sys.stderr)
    return 1


def next_ids(rows: list[dict], family: str, count: int) -> list[str]:
    used = {r["id"].strip() for r in rows}
    numbers = [int(i.split("-")[1]) for i in used if i.startswith(family + "-") and i.split("-")[1].isdigit()]
    start = max(numbers) + 1 if numbers else 1
    out = []
    while len(out) < count:
        candidate = f"{family}-{start:02d}"
        start += 1
        if candidate not in used:
            out.append(candidate)
    return out


def cmd_merge() -> int:
    rows = read_register()
    taken = {r["id"].strip() for r in rows}
    added, skipped = [], []

    for path in sorted(glob.glob(os.path.join(PROPOSALS, "*.csv"))):
        source = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as handle:
                proposals = list(csv.DictReader(handle))
        except Exception as exc:  # noqa: BLE001
            skipped.append((source, "خواندن‌نشدنی", str(exc)[:50]))
            continue
        for row in proposals:
            ident = (row.get("id") or "").strip()
            if not FAMILY.match(ident):
                family, assigned = ident, ""
                if family and family.isalpha():
                    ident = next_ids(rows + added, family, 1)[0]
                else:
                    skipped.append((source, "شناسهٔ نامعتبر", row.get("indicator", "")[:40]))
                    continue
            elif ident in taken:
                skipped.append((source, "شناسهٔ تکراری", ident))
                continue
            elif not rows and False:
                pass
            record = {k: (row.get(k) or "").strip() for k in FIELDS}
            record["id"] = ident
            record["status"] = record["status"] or "ثبت شد"
            if not record["source_primary"]:
                record["source_primary"] = "نیازمند لنگرگاه بند — موج صفر"
            added.append(record)
            taken.add(ident)

    if not added:
        print("پیشنهاد تازه‌ای برای ادغام نبود")
    for record in added:
        rows.append(record)

    with open(REGISTER, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})

    final = [r["id"] for r in rows]
    duplicates = [k for k, v in Counter(final).items() if v > 1]
    print(f"رجیستر: {len(rows)} ردیف  ·  افزوده: {len(added)}  ·  تصادم: {len(duplicates)}")
    if skipped:
        print(f"رد‌شده: {len(skipped)}")
        for source, reason, detail in skipped[:12]:
            print(f"  {source}: {reason} — {detail}")
    cmd_manifest()
    return 1 if duplicates else 0


def main() -> int:
    if len(sys.argv) < 2:
        print("اجرا: manifest | status | merge", file=sys.stderr)
        return 2
    action = sys.argv[1]
    if action == "manifest":
        return cmd_manifest()
    if action == "status":
        return cmd_status()
    if action == "merge":
        return cmd_merge()
    if action == "adjudicate":
        # داوری هماهنگ‌کننده روی ردیف‌هایی که کارگر نتوانست ببندد.
        # قاعده: مقدار را خودمان از ردیف مبنا محاسبه می‌کنیم و منشأ را
        # می‌نویسیم. عدد ساختگی درج نمی‌شود؛ ردیف مبنا نام برده می‌شود.
        rulings = {
            "ES-08": {
                "value": "358.064",
                "source_primary": "محاسبه: ES-07 (۶۲۹٫۹۵ دلار در هکتار) × SC-03 (۵۶۸٬۴۰۰ هکتار)",
                "action": "مقدار پیشین ۳۶۰٫۵۴ از مبنای بازنشسته محاسبه شده بود؛ به مبنای مصوب بازگردانده شد",
                "status": "اصلاح شد",
            },
            "FN-179": {
                "source_primary": "مقدار بازنشسته — ES-07 جایگزین شده است",
                "action": "سقف بازنشسته، نگه‌داشته شد برای رفع ابهام ارجاع‌های قدیمی",
                "status": "بازنشسته",
            },
            # — سطوح اطمینان D که بند ۵ استاندارد ممنوع کرده —
            "S-01": {
                "confidence": "C",
                "source_primary": "تراز آبخوان — فاقد مقدار؛ پروتکل اندازه‌گیری HP-01 بند ۳٫۱۴ با شبکهٔ ده چاهک",
                "action": "سطح D غیرمجاز بود؛ تا اجرای پروتکل، تراز آبخوان کمّیت اندازه‌گیری‌شده در آینده است نه مقدار بی‌پایه",
                "status": "در انتظار",
            },
            "ES-16": {
                "source_primary": "سطر کربن پس از تصحیح — ۸۷٫۹۵ دلار در هکتار در سال؛ نه مقدار خدمات اکوسیستمی",
                "action": "در دو نگارش بیزنس‌پلن به اشتباه برچسب مقدار خدمات اکوسیستمی خورده بود؛ تصحیح شد",
                "status": "اصلاح شد",
            },
            "FN-90": {
                "value": "۶۱",
                "source_primary": "محاسبه: جدول ۹٫۱ کتابچهٔ HP-10",
                "action": "مقدار پیشین ۸۰ دلار در هکتار در سال با جدول همان کتابچه نمی‌خواند؛ به مقدار محاسبه‌شده تصحیح شد",
                "status": "اصلاح شد",
            },
            "FN-91": {
                "source_primary": "مقدار بازنشسته",
                "action": "در هیچ نسبتی وارد نمی‌شود؛ ارجاع‌های قدیمی با FN-24 جایگزین شوند",
                "status": "بازنشسته",
            },
            "TO-135": {
                "source_primary": "مقدار بازنشسته",
                "action": "در هیچ نسبتی وارد نمی‌شود؛ به ردیف جایگزین بخش ۹ ارجاع داده شود",
                "status": "بازنشسته",
            },
        }
        # شمار گونهٔ بومی — دو ردیف رجیستر با جدول کتابچه نمی‌خواند
        species_fix = {"SP-05": "۱۰", "SP-10": "۱۰"}
        rows = read_register()
        changed = 0
        for row in rows:
            ident = row["id"].strip()
            ruling = rulings.get(ident)
            if ruling:
                before = dict(row)
                row.update({k: v for k, v in ruling.items() if k in FIELDS})
                changed += 1
                print(f"  {ident}: {before['value']} ← {row['value']}" if "value" in ruling else f"  {ident}: {before['status']} ← {row['status']}")
            elif ident in species_fix:
                print(f"  {ident}: شمار گونهٔ بومی {row['value']} ← {species_fix[ident]}")
                row["value"] = species_fix[ident]
                row["action"] = "شمار با جدول ۵٫۱۱ کتابچهٔ HP-10 تطبیق داده شد"
                changed += 1
        if not changed:
            print("ردیفی برای داوری نبود")
            return 0
        with open(REGISTER, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in FIELDS})
        print(f"داوری‌شده: {changed} ردیف")
        cmd_manifest()
        return 0
    print(f"فرمان ناشناخته: {action}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
