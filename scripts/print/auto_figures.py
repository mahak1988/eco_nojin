"""جفت‌کردن خودکار شکل‌های عددی با جدول‌های منبع.

قرارداد نگارشی کتابچه‌ها این است: شکلِ شمارهٔ N.M در فصل N، از جدولِ
شمارهٔ N.M همان فصل می‌آید. پس برای شکلی که عنوانش واژهٔ عددی دارد
(نمودار، منحنی، مقایسه، هزینه، سالانه، تحلیل)، نزدیک‌ترین جدولِ عددیِ
پیش از آن در همان فصل دادهٔ منبع است.

خروجی: به figures_data.json اضافه می‌شود. هیچ عددی ساخته نمی‌شود؛
هر مقدار عیناً از سلول جدول خوانده می‌شود و برچسب اطمینان از سطر
«منبع:» همان جدول برداشته می‌شود.

اجرا:
    python scripts/print/auto_figures.py            # پیش‌نمایش
    python scripts/print/auto_figures.py --write    # نوشتن در figures_data.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import parse

DATA = os.path.join(HERE, "figures_data.json")

# نمودارهایی که دستی و با جفت‌سازی تأییدشده ساخته شده‌اند و نباید بازنویسی شوند
MANUAL_IDS = {("HP-17", "۹.۱")}

# واژه‌هایی که نشان می‌دهند شکل، دادهٔ عددی دارد
NUMERIC_HINT = re.compile(
    r"نمودار|منحنی|هزینه|فایده|درآمد|منفعت|مقایسه|تحلیل|سالانه|"
    r"توزیع|بازه|تغییر|روند|سالانه|ظرفیت|حجم|بار|دبی|تنش|تن",
)
# شکل‌هایی که ذاتاً مفهومی‌اند و دادهٔ عددی ندارند
CONCEPTUAL = re.compile(
    r"فلوچارت|نقشه|زنجیره|ساختار|مقطع|پلان|شماتیک|دیاگرام|نوار|"
    r"حلقه|چرخه|سلسله|درخت|شبکه|جایگاه|معماری|روند|نقشهٔ",
)
CONF_RE = re.compile(r"سطح اطمینان\s*:\s*([^\n·]+)")
RE_LATIN_ID = re.compile(r"^[\d.٫۰-۹]+$")


def chapter_of(doc) -> list:
    """شمارهٔ فصل هر بلوک را برمی‌گرداند."""
    out, cur = [], "۰"
    for b in doc.front + doc.body:
        if b["t"] == "chapter":
            cur = parse.norm_num(b.get("n", "۰"))
        out.append(cur)
    return out


def numeric_profile(rows: list) -> tuple:
    """(تعداد ستون، تعداد سطر، آیا سری زمانی/دسته‌ای است)"""
    if len(rows) < 3:
        return 0, len(rows), False
    head = rows[0]
    body = rows[1:]
    numcols = 0
    for c in range(len(head)):
        col = [r[c] for r in body if len(r) > c]
        vals = [parse.num(v) for v in col if v.strip()]
        if len(vals) >= max(2, len(col) * 0.5) and vals:
            numcols += 1
    return numcols, len(body), numcols >= 2


def label_of(v: str) -> str:
    return re.sub(r"^[0-9۰-۹.٫\s]+", "", v.strip()) or v.strip()


def to_series(tb: dict) -> dict | None:
    rows = tb["rows"]
    if len(rows) < 3:
        return None
    head, body = rows[0], rows[1:]
    # ستون نخست برچسب ردیف است
    labels = [label_of(r[0]) for r in body]
    series = []
    for c in range(1, len(head)):
        col = [(r[c] if len(r) > c else "") for r in body]
        vals = [parse.num(v) for v in col]
        if sum(1 for v in vals if v is not None) < 2:
            continue
        series.append({"name": head[c].strip() or f"ستون {c}", "y": vals})
    if not series:
        return None
    return {"x": labels, "series": series}


def conf_of(tb: dict) -> str:
    src = tb.get("src") or ""
    m = CONF_RE.search(src)
    tail = src.split("·")[-1].strip() if "·" in src else ""
    if m:
        return f"سطح اطمینان {m.group(1).strip()}"
    if tail:
        return tail[:80]
    for r in tb["rows"]:
        for c in r:
            if "سطح اطمینان" in c:
                m2 = CONF_RE.search(c)
                if m2:
                    return f"سطح اطمینان {m2.group(1).strip()}"
    return ""


def pick_table(fig, cands):
    """انتخاب جدول منبع — فقط وقتی جفت‌سازی قوی باشد.

    قرارداد نگارشی کتابچه‌ها: شکل N.M از جدول N.M همان فصل می‌آید.
    پس جفت‌سازی تنها وقتی پذیرفته می‌شود که شمارهٔ فصل شکل و شمارهٔ فصل
    جدول یکی باشد. جفت‌سازی ضعیف (نزدیک‌ترین جدول) رد می‌شود، چون نمودار
    غلط در سند فنی از جای‌نگهدارِ صریح بدتر است.
    """

    def chap(x):
        return (x or "").split(".")[0].split("٫")[0].strip()

    fch = chap(fig.get("id"))
    same = [t for t in cands if chap(t.get("id")) == fch]
    if not same:
        return None, "رد — شمارهٔ فصل جدول با شکل نمی‌خواند"
    # اگر عنوان یا شرح، جدول مشخصی را نام برده، همان برنده است
    text = fig.get("x", "") + " " + fig.get("desc", "")
    named = re.findall(r"جدول\s+([۰-۹0-9]+(?:[.٫][۰-۹0-9]+)*)", text)
    if named:
        want = parse.norm_num(named[0])
        for t in same:
            if t.get("id") and parse.norm_num(t["id"]) == want:
                return t, "عنوان شکل جدول را نام برده"
    prior = [t for t in same if t["line"] < fig["line"]]
    if prior:
        return prior[-1], "نزدیک‌ترین جدول هم‌شمارهٔ فصل"
    return same[0], "نخستین جدول هم‌شمارهٔ فصل"


def harvest(path: str) -> list:
    doc = parse.load(path)
    book = os.path.splitext(os.path.basename(path))[0][:5]
    blocks = doc.front + doc.body
    chaps = chapter_of(doc)

    # جدول‌های عددی به تفکیک فصل
    numtabs: dict[str, list] = {}
    for b, ch in zip(blocks, chaps, strict=False):
        if b["t"] != "table" or b.get("bare"):
            continue
        _ncol, nrow, ok = numeric_profile(b["rows"])
        if ok and nrow >= 2:
            numtabs.setdefault(ch, []).append(b)

    out = []
    for b, ch in zip(blocks, chaps, strict=False):
        if b["t"] != "figure":
            continue
        title = b.get("x", "")
        if CONCEPTUAL.search(title) and not NUMERIC_HINT.search(title):
            continue
        if not NUMERIC_HINT.search(title):
            continue
        cands = numtabs.get(ch) or []
        if not cands:
            continue
        tb, why = pick_table(b, cands)
        if tb is None:
            continue
        ser = to_series(tb)
        if not ser:
            continue
        out.append(
            {
                "id": b["id"],
                "book": book,
                "kind": "grouped_bar" if len(ser["series"]) > 1 else "line",
                "title": title.strip()[:90],
                "x_label": ser["x"][0][:28] if ser["x"] else "",
                "y_label": tb["rows"][0][1].strip()[:34] if len(tb["rows"][0]) > 1 else "",
                "x": ser["x"][:12],
                "series": ser["series"][:6],
                "conf": conf_of(tb),
                "source": (
                    f"جدول {tb['id']} سطر {tb['line']}" if tb.get("id") else f"سطر {tb['line']}"
                )
                + f" — {why}",
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--book", default="")
    args = ap.parse_args()

    found = []
    for f in sorted(os.listdir(parse.BOOKS)):
        if not f.endswith(".txt"):
            continue
        if args.book and not f.startswith(args.book):
            continue
        found.extend(harvest(os.path.join(parse.BOOKS, f)))

    # یکتا کردن بر پایهٔ (سند، شمارهٔ شکل) — نخستین انتخاب حفظ می‌شود
    seen, uniq = set(), []
    for s in found:
        key = (s["book"], s["id"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(s)
    dropped = len(found) - len(uniq)
    found = uniq

    for s in found:
        print(
            f"  {s['book']:<7} شکل {s['id']:<8} {len(s['series'])} سری × {len(s['x'])} نقطه"
            f"  ·  {s['source']}  ·  {s['conf'][:38]}"
        )

    print(f"\nقابل رسم: {len(found)} شکل  ·  تکراریِ حذف‌شده: {dropped}")
    if args.write and found:
        # نمودارهای دست‌ساز مقدم‌اند و بازنویسی نمی‌شوند
        manual = []
        if os.path.exists(DATA):
            with open(DATA, encoding="utf-8") as _fh:
                cur = json.load(_fh)
            cur = cur.get("specs", []) if isinstance(cur, dict) else cur
            for s in cur:
                if (s.get("book"), s.get("id")) in MANUAL_IDS:
                    manual.append(s)
        keep = {(s["book"], s["id"]) for s in manual}
        merged = manual + [s for s in found if (s["book"], s["id"]) not in keep]
        doc = {
            "_meta": {
                "generator": "auto_figures.py",
                "rule": "شمارهٔ فصل شکل و شمارهٔ فصل جدول باید یکی باشد؛ "
                "نمودار غلط از جای‌نگهدار بدتر است",
                "manual": sorted(MANUAL_IDS),
            },
            "specs": merged,
        }
        with open(DATA, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        print(f"نوشته شد: {DATA}  ·  دستی {len(manual)} + خودکار {len(merged) - len(manual)}")
    elif not args.write:
        print("برای نوشتن: --write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
