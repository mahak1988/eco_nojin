"""هماهنگ‌کنندهٔ ساخت نسخهٔ چاپی — طرح هیدروما نوژین.

مسیر: کتابچه/جلد متنی ← پارسر ← HTML + CSS ← چاپ بی‌نمایش مرورگر ← PDF

کاربرد:
    python scripts/print/build.py                 # همهٔ اسناد
    python scripts/print/build.py --only HP-17    # یک سند
    python scripts/print/build.py --no-pdf        # فقط HTML
    python scripts/print/build.py --report        # فقط گزارش، بدون ساخت
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import parse

OUT = os.path.abspath(os.path.join(HERE, "..", "..", "چاپ"))
PDFDIR = os.path.join(OUT, "pdf")
HTMLDIR = os.path.join(OUT, "html")
FIGDIR = os.path.join(HERE, "figures")

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# ترتیب چاپ: جلدها پیش از کتابچه‌ها
VOLUMES = [
    "راهبردی هیدروما.txt",
    "مهندسی هیدروما.txt",
    "سند مرجع.txt",
    "توجیهی فنی اقتصادی.txt",
    "راهنمای نقشه برداری.txt",
    "بیزنس-پلن-شرکت.txt",
]


def targets() -> list[str]:
    files = [f for f in os.listdir(parse.BOOKS) if f.startswith("HP-") and f.endswith(".txt")]
    files.sort()
    return [
        os.path.join(parse.BOOKS, v)
        for v in VOLUMES
        if os.path.exists(os.path.join(parse.BOOKS, v))
    ] + [os.path.join(parse.BOOKS, f) for f in files]


def find_browser() -> str | None:
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    return None


def slug(name: str) -> str:
    base = os.path.splitext(name)[0]
    return re.sub(r"[^\w۰-۹\-]+", "-", base, flags=re.UNICODE).strip("-")


def to_pdf(browser: str, html_path: str, pdf_path: str, timeout: int = 300) -> bool:
    url = "file:///" + html_path.replace("\\", "/")
    prof = os.path.join(OUT, ".profile")
    os.makedirs(prof, exist_ok=True)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=20000",
        "--disable-extensions",
        f"--user-data-dir={prof}",
        f"--print-to-pdf={pdf_path}",
        url,
    ]
    try:
        subprocess.run(cmd, timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired:
        return False
    return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 2000


def page_info(pdf_path: str) -> dict:
    with open(pdf_path, "rb") as _fh:
        d = _fh.read()
    pages = len(re.findall(rb"/Type\s*/Page[^s]", d))
    boxes = re.findall(rb"/MediaBox\s*\[\s*([\d\.\s]+?)\]", d)
    land = 0
    for b in boxes:
        try:
            v = [float(x) for x in b.split()]
            if v[2] > v[3]:
                land += 1
        except ValueError:
            pass
    return {"pages": pages, "landscape": land, "pdf_kb": len(d) // 1024}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="نام کوتاه سند، مثل HP-17")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    os.makedirs(HTMLDIR, exist_ok=True)
    os.makedirs(PDFDIR, exist_ok=True)
    shutil.copy(os.path.join(HERE, "book.css"), OUT)

    if os.path.isdir(FIGDIR):
        dst = os.path.join(OUT, "figures")
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(FIGDIR, dst)
    else:
        os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)

    browser = None if args.no_pdf else find_browser()
    if not args.no_pdf and not browser:
        print("مرورگر یافت نشد — فقط HTML ساخته می‌شود")
        browser = ""

    rows = []
    t0 = time.time()
    for path in targets():
        name = os.path.basename(path)
        if args.only and args.only not in name:
            continue
        doc = parse.load(path)
        html_text, ph = parse.build_html(doc)
        hp = os.path.join(HTMLDIR, slug(name) + ".html")
        with open(hp, "w", encoding="utf-8") as f:
            f.write(html_text)

        rec = {
            "name": name,
            "lines": doc.stats["lines"],
            "chapters": doc.stats["chapters"],
            "sections": doc.stats["sections"],
            "tables": doc.stats["tables"],
            "wide": doc.stats["wide_tables"],
            "figures": doc.stats["figures"],
            "figure_pending": ph,
            "formulas": doc.stats["formulas"],
            "html_kb": len(html_text.encode("utf-8")) // 1024,
            "pages": 0,
            "landscape": 0,
            "pdf_kb": 0,
        }
        if browser and not args.report:
            pp = os.path.join(PDFDIR, slug(name) + ".pdf")
            if os.path.exists(pp):
                os.remove(pp)
            if to_pdf(browser, hp, pp):
                rec.update(page_info(pp))
        rows.append(rec)
        print(
            f"  {name[:34]:<36} سطر {rec['lines']:>5}  فصل {rec['chapters']:>2}  "
            f"جدول {rec['tables']:>3}  افقی {rec['wide']:>2}  شکل {rec['figures']:>2}"
            f"  ·  صفحه {rec['pages']:>3}"
        )

    with open(os.path.join(OUT, "build-report.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    def tot(k):
        return sum(r[k] for r in rows)

    print("\n" + "─" * 74)
    print(
        f"سند: {len(rows)} · سطر: {tot('lines'):,} · فصل: {tot('chapters')} · "
        f"جدول: {tot('tables'):,} · جدول افقی: {tot('wide')} · شکل: {tot('figures'):,}"
    )
    print(
        f"شکل رسم‌نشده: {tot('figure_pending'):,} از {tot('figures'):,}  ·  "
        f"فرمول: {tot('formulas'):,}"
    )
    if tot("pages"):
        print(
            f"صفحهٔ چاپی: {tot('pages'):,}  ·  صفحهٔ افقی: {tot('landscape')}  ·  "
            f"حجم: {tot('pdf_kb'):,} کیلوبایت"
        )
    print(f"زمان: {time.time() - t0:.0f} ثانیه  ·  خروجی: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
