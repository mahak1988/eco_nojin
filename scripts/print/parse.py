"""پارسر قالب متنی کتابچه‌های طرح هیدروما نوژین.

قالب مبدأ سفارشی است و با هیچ نشانه‌گذاری استانداردی نمی‌خواند:
  - عنوان فصل در بدنه: «فصل ۳ — شناخت مدل‌های محاسباتی» (خط تیره)
  - فصل در فهرست مطالب: «فصل ۳: شناخت…» (دونقطه) — بدنه نیست
  - بند: «۱.۱ معرفی کلی» یا «۱.۱ .۱ سه گزارهٔ حاکم» (فاصلهٔ سخت پیش از نقطه)
  - جدول: خط عنوان «جدول ۹.۱ — …» و سپس سطرهای جداشده با TAB
  - شکل: خط عنوان «شکل ۹.۱ — …» و سپس سطر «تحلیل شکل: …»
  - منبع: «منبع: …» در سطر پس از جدول
  - فرمول: «فرمول …» یا سطرهایی که با شناسهٔ F شروع و TAB دارند

هیچ جداکنندهٔ سرستون و هیچ کادری در قالب نیست؛ سطر نخستِ پس از عنوان، سرستون است.
"""

from __future__ import annotations

import html
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BOOKS = os.path.join(ROOT, "کتابها")

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

# «بند ۳.۳ .۳» → «بند ۳.۳.۳»
NUM_LEVEL = r"[۰-۹0-9]+"
SEP = r"[.٫٫]"

RE_CHAPTER_BODY = re.compile(r"^\s*فصل\s+(" + NUM_LEVEL + r")\s*[—–\-]\s*(.+?)\s*$")
RE_CHAPTER_TOC = re.compile(r"^\s*فصل\s+(" + NUM_LEVEL + r")\s*:\s*(.+?)\s*$")
RE_SECTION = re.compile(
    r"^\s*(" + NUM_LEVEL + r"(?:\s*[.٫]\s*" + NUM_LEVEL + r")+)\s*[.٫]?\s+(\S.*)$"
)
RE_SECTION_SUFFIX = re.compile(r"^\s*(" + NUM_LEVEL + r")\s+(\S.*)$")
RE_TABLE_CAP = re.compile(r"^\s*(جدول)\s+(\S+)\s*[—–\-]\s*(.+?)\s*$")
RE_TABLE_CAP_PLAIN = re.compile(r"^\s*(جدول)\s+(\S.*)$")
RE_FIG_CAP = re.compile(r"^\s*شکل\s+(\S+)\s*[—–\-]\s*(.+?)\s*$")
RE_FIG_CAP_PLAIN = re.compile(r"^\s*شکل\s+(\S.*)$")
# «نمودار ۹.۱ — …» در HP-08 و چند جلد، همان نقش «شکل» را دارد
RE_FIG_KIND_CAP = re.compile(r"^\s*نمودار\s+(\S+)\s*[—–\-]\s*(.+?)\s*$")
RE_FIG_DESC = re.compile(r"^\s*(تحلیل شکل|این شکل|شکل\s+\S+\s+نشان)")
RE_FORMULA_CAP = re.compile(r"^\s*فرمول\s+(\S.*)$")
RE_FORMULA_ROW = re.compile(r"^\s*(F\d+[A-Za-z۰-۹]?)\t")
RE_SOURCE = re.compile(r"^\s*منبع[:：]")
RE_APPENDIX = re.compile(r"^\s*(پیوست\s+[الفبپجچ]|جدول\s+الف|جدول\s+خ\s|جدول\s+پ\s)")
RE_RULE = re.compile(r"^\s*[-=_—–]{4,}\s*$")

WIDE_COLS = 8          # بیش از این تعداد ستون → صفحهٔ افقی
MAX_COLS = 14          # سقف نمایش؛ فراتر از آن ستون‌های خالی حذف می‌شوند
MAX_ROWS = 400         # سقف بلعیدن سطر در یک جدول — جلوگیری از بلعیدن کل سند

RE_BOXART = re.compile(r"[─-╿]")
RE_LATIN_NUM = re.compile(r"[0-9]")


def fa_to_latin(s: str) -> str:
    return s.translate(str.maketrans(FA_DIGITS, "0123456789"))


def latin_to_fa(s: str) -> str:
    return s.translate(str.maketrans("0123456789", FA_DIGITS))


def num(s: str):
    """«۱۲٫۵» → 12.5 ؛ اگر عدد نبود None."""
    t = fa_to_latin(s).replace("٫", ".").replace(",", "").strip()
    try:
        return float(t)
    except ValueError:
        return None


def norm_num(s: str) -> str:
    """«۱.۱ .۱» → «۱.۱.۱» ؛ ارقام فارسی نگه داشته می‌شود."""
    return re.sub(r"\s*[.٫]\s*", ".", s.strip())


def is_numeric_cell(s: str) -> bool:
    t = s.strip()
    if not t:
        return False
    t = re.sub(r"[−\-+،,]", "", t)
    t = fa_to_latin(t)
    t = t.replace("٫", ".").replace("%", "").replace("٬", "")
    t = re.sub(r"\s*[/×÷]\s*\d+\s*$", "", t)
    return bool(re.match(r"^\d+(\.\d+)?$", t.strip()))


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def cell_html(s: str) -> str:
    s = s.strip()
    if not s:
        return '<td class="empty"></td>'
    cls = ' class="num"' if is_numeric_cell(s) else ""
    inner = esc(s)
    # شناسه‌های رجیستری و کدها باید چپ‌به‌راست بمانند
    if re.search(r"\b(FN|ES|TO|PL|SC|ID|ST|MD|GV|CB|PR|NS|EM|SR|MR|RR|HPX|HP|MC|G|S|R|AT|M)-\d", s):
        for tok in re.findall(
            r"\b(?:FN|ES|TO|PL|SC|ID|ST|MD|GV|CB|PR|NS|EM|SR|MR|RR|HPX|HP|MC|G|S|R|AT|M)-[0-9۰-۹]+[A-Za-z]?",
            s,
        ):
            inner = inner.replace(esc(tok), f'<span class="hdr-id">{esc(tok)}</span>')
    return f"<td{cls}>{inner}</td>"


def head_html(s: str) -> str:
    s = s.strip()
    if not s:
        return "<th></th>"
    return f"<th>{esc(s)}</th>"


class Doc:
    def __init__(self, path: str):
        self.path = path
        self.name = os.path.basename(path)
        self.book = os.path.splitext(self.name)[0][:5]
        self.lines = open(path, encoding="utf-8").read().split("\n")
        self.cover: dict = {}
        self.front: list = []
        self.toc: list = []
        self.body: list = []
        self.stats: dict = {
            "chapters": 0, "sections": 0, "tables": 0, "wide_tables": 0,
            "figures": 0, "figure_placeholders": 0, "formulas": 0,
            "lines": len(self.lines),
        }

    # ── خواندن ──────────────────────────────────────────
    def parse(self):
        n = len(self.lines)
        chaps = self._chapter_lines()
        first = chaps[0] if chaps else 0
        i = 0
        while i < first:
            i = self._front(self.lines[i], i)
        while i < n:
            i = self._body_block(i)
        return self

    def _chapter_lines(self):
        """فهرست فصل‌های بدنه.

        فهرست مطالبِ کتابچه‌ها با دونقطه می‌آید («فصل ۱: …») و فصل بدنه با
        خط تیره («فصل ۱ — …»)، پس الگوی خط تیره خودش کافی است. اما چند جلد
        فهرستشان هم خط تیره دارد. برای آن‌ها قاعدهٔ «آخرین تکرار هر شماره» است:
        فصل بدنه همواره پس از فهرست می‌آید.
        """
        last: dict[str, int] = {}
        for i, line in enumerate(self.lines):
            m = RE_CHAPTER_BODY.match(line)
            if not m:
                continue
            if len(line.strip()) > 120:
                continue
            last[norm_num(m.group(1))] = i
        return sorted(last.values())

    def _front(self, raw: str, i: int):
        s = raw.strip()
        if not s:
            return i + 1
        m = RE_CHAPTER_TOC.match(raw)
        if m:
            self.toc.append((norm_num(m.group(1)), m.group(2).strip()))
            return i + 1
        if "\t" in raw:
            # جدول پیش از نخستین فصل: تاریخچهٔ نسخه یا شناسنامه
            rows = []
            j = i
            while j < len(self.lines) and self.lines[j].strip() and "\t" in self.lines[j] and len(rows) < MAX_ROWS:
                rows.append(self.lines[j].rstrip("\n").split("\t"))
                j += 1
            if len(rows) >= 2:
                ncol = max(len(r) for r in rows)
                rows = [r + [""] * (ncol - len(r)) for r in rows]
                self.stats["tables"] += 1
                self.front.append(
                    {"t": "table", "kind": "جدول", "id": "", "x": "سربرگ و تاریخچهٔ سند",
                     "rows": rows, "ncol": ncol, "src": None,
                     "wide": ncol > WIDE_COLS, "bare": True, "line": i + 1}
                )
            return j
        # فیلدهای سرصفحه
        for key, pat in (
            ("نسخه", r"^نسخه[:：]\s*(.+)$"),
            ("تاریخ تدوین", r"^تاریخ تدوین[:：]\s*(.+)$"),
            ("متولی", r"^متولی[:：]\s*(.+)$"),
        ):
            mm = re.match(pat, s)
            if mm and key not in self.cover:
                self.cover[key] = mm.group(1).strip()
        mm = re.match(r"^کد سند[:：]\s*(.+)$", s)
        if mm:
            self.cover["کد سند"] = mm.group(1).strip()
        if re.match(r"^دارایی", s) or re.match(r"^\d+\s*شکل", s) or re.match(r"^شمار", s):
            self.cover.setdefault("اعلام دارایی", s)
        if re.match(r"^(بازگشت|هزینه|دوره)", s):
            self.cover.setdefault("خلاصهٔ مالی", s)
        self.front.append({"t": "p", "x": s, "line": i + 1})
        return i + 1

    def _body_block(self, i: int) -> int:
        lines = self.lines
        s = lines[i].strip()

        if not s:
            return i + 1

        m = RE_CHAPTER_BODY.match(lines[i])
        if m:
            self.stats["chapters"] += 1
            self.body.append({"t": "chapter", "n": m.group(1), "x": m.group(2), "line": i + 1})
            return i + 1

        # «نمودار» نقش شکل دارد، نه جدول — پیش از الگوی جدول بررسی می‌شود
        m = RE_FIG_KIND_CAP.match(lines[i])
        if m:
            return self._figure(i, m)

        # سطرِ بدون عنوانِ جدولی که خودش سرستون است
        if "\t" in lines[i]:
            return self._bare_table(i)

        # جدول: خط عنوان + سطرهای TAB
        m = RE_TABLE_CAP.match(lines[i]) or RE_TABLE_CAP_PLAIN.match(lines[i])
        if m:
            return self._table(i, m)

        m = RE_FIG_CAP.match(lines[i]) or RE_FIG_CAP_PLAIN.match(lines[i])
        if m:
            return self._figure(i, m)

        if RE_FORMULA_ROW.match(lines[i]):
            return self._formula(i)

        m = RE_FORMULA_CAP.match(lines[i])
        if m:
            self.stats["formulas"] += 1
            self.body.append({"t": "formula", "x": m.group(1), "line": i + 1})
            return i + 1

        if RE_SOURCE.match(lines[i]):
            self.body.append({"t": "src", "x": s, "line": i + 1})
            return i + 1

        if RE_FIG_DESC.match(lines[i]):
            self.body.append({"t": "figdesc", "x": s, "line": i + 1})
            return i + 1

        m = RE_SECTION.match(lines[i])
        if m and len(m.group(1)) <= 26:
            label, title = norm_num(m.group(1)), m.group(2).strip()
            depth = label.count(".") + 1
            self.stats["sections"] += 1
            self.body.append(
                {"t": "sec", "label": label, "x": title, "d": depth, "line": i + 1}
            )
            return i + 1

        if RE_RULE.match(lines[i]):
            return i + 1

        if RE_APPENDIX.match(lines[i]):
            self.body.append({"t": "appendix", "x": s, "line": i + 1})
            return i + 1

        self.body.append({"t": "p", "x": s, "line": i + 1})
        return i + 1

    # ── جدول ────────────────────────────────────────────
    def _table(self, i: int, m) -> int:
        lines = self.lines
        kind, ident, title = m.group(1), m.group(2), m.group(3) if m.lastindex and m.lastindex >= 3 else m.group(2)
        rows = []
        j = i + 1
        while j < len(lines) and lines[j].strip() and "\t" in lines[j] and len(rows) < MAX_ROWS:
            rows.append(lines[j].rstrip("\n").split("\t"))
            j += 1
        src = None
        if j < len(lines) and RE_SOURCE.match(lines[j]):
            src = lines[j].strip()
            j += 1
        if rows:
            ncol = max(len(r) for r in rows)
            rows = [r + [""] * (ncol - len(r)) for r in rows]
            # ستون‌های کاملاً خالی انتهایی حذف می‌شود
            while ncol > 1 and all(not r[ncol - 1].strip() for r in rows):
                rows = [r[: ncol - 1] for r in rows]
                ncol -= 1
            while ncol > MAX_COLS:
                rows = [r[:MAX_COLS] for r in rows]
                ncol = MAX_COLS
        else:
            ncol = 0
        self.stats["tables"] += 1
        wide = ncol > WIDE_COLS
        if wide:
            self.stats["wide_tables"] += 1
        self.body.append(
            {
                "t": "table", "kind": kind, "id": ident.strip(),
                "x": title.strip(), "rows": rows, "ncol": ncol,
                "src": src, "wide": wide, "line": i + 1,
            }
        )
        return j

    # ── شکل ─────────────────────────────────────────────
    def _figure(self, i: int, m) -> int:
        lines = self.lines
        ident = m.group(1)
        title = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
        desc = []
        j = i + 1
        while j < len(lines) and len(desc) < 3:
            s = lines[j].strip()
            if not s:
                j += 1
                continue
            if RE_FIG_DESC.match(lines[j]) or (desc and not self._is_structural(s)):
                desc.append(s)
                j += 1
                continue
            break
        self.stats["figures"] += 1
        self.body.append(
            {"t": "figure", "id": ident.strip(), "x": title.strip(),
             "desc": " ".join(desc), "line": i + 1}
        )
        return j

    def _is_structural(self, s: str) -> bool:
        return bool(
            RE_CHAPTER_BODY.match(s) or RE_TABLE_CAP.match(s) or RE_TABLE_CAP_PLAIN.match(s)
            or RE_FIG_CAP.match(s) or RE_FIG_CAP_PLAIN.match(s) or RE_SOURCE.match(s)
            or RE_SECTION.match(s) or RE_RULE.match(s) or RE_APPENDIX.match(s)
        )

    def _is_body_chapter(self, i: int) -> bool:
        lines = self.lines
        if len(lines[i].strip()) > 120:
            return False
        before_ok = i == 0 or not lines[i - 1].strip()
        after_ok = i + 1 >= len(lines) or not lines[i + 1].strip()
        return before_ok and after_ok

    # ── جدول بی‌عنوان ───────────────────────────────────
    def _bare_table(self, i: int) -> int:
        """سطرهای جداشده با TAB که خط عنوان ندارند — سند مرجع و جلدها."""
        lines = self.lines
        rows = []
        j = i
        while j < len(lines) and lines[j].strip() and "\t" in lines[j] and len(rows) < MAX_ROWS:
            rows.append(lines[j].rstrip("\n").split("\t"))
            j += 1
        # یک سطرِ تک‌افتاده بهتر است متن بماند تا جدول یک‌سطری ساخته شود
        if len(rows) < 2:
            self.body.append({"t": "p", "x": lines[i].strip().replace("\t", " · "), "line": i + 1})
            return i + 1
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        while ncol > 1 and all(not r[ncol - 1].strip() for r in rows):
            rows = [r[: ncol - 1] for r in rows]
            ncol -= 1
        while ncol > MAX_COLS:
            rows = [r[:MAX_COLS] for r in rows]
            ncol = MAX_COLS
        self.stats["tables"] += 1
        wide = ncol > WIDE_COLS
        if wide:
            self.stats["wide_tables"] += 1
        # آخرین سطرِ پیش از منبع، معمولاً «مجموع» است
        self.body.append(
            {"t": "table", "kind": "جدول", "id": "", "x": "",
             "rows": rows, "ncol": ncol, "src": None, "wide": wide, "bare": True, "line": i + 1}
        )
        return j

    # ── فرمول ───────────────────────────────────────────
    def _formula(self, i: int) -> int:
        lines = self.lines
        parts = lines[i].rstrip("\n").split("\t")
        fid = parts[0].strip()
        expr = parts[1].strip() if len(parts) > 1 else ""
        note = parts[2].strip() if len(parts) > 2 else ""
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        self.stats["formulas"] += 1
        self.body.append(
            {"t": "formula", "id": fid, "x": expr, "note": note, "line": i + 1}
        )
        return j


# ── نمودارسازی HTML ────────────────────────────────────

def render_table(tb: dict, fignum: dict) -> str:
    kind = tb["kind"]
    if tb.get("bare") or not tb.get("x"):
        cap = ""
    else:
        cap = f'<span class="tno">{esc(kind)} {esc(tb["id"])}</span> — {esc(tb["x"])}'
    open_tag = f"<table><caption>{cap}</caption>" if cap else "<table>"
    out = [open_tag]
    rows = tb["rows"]
    if not rows:
        out.append("</table>")
        return "\n".join(out)
    out.append("<thead><tr>" + "".join(head_html(c) for c in rows[0]) + "</tr></thead><tbody>")
    for r in rows[1:]:
        cells = "".join(cell_html(c) for c in r)
        cls = ""
        joined = "".join(r).replace(" ", "")
        if "مجموع" in joined or "جمع" in joined:
            cls = ' class="total"'
        out.append(f"<tr{cls}>{cells}</tr>")
    out.append("</tbody></table>")
    if tb.get("src"):
        out.append(f'<p class="src">{esc(tb["src"])}</p>')
    return "\n".join(out)


def render_block(b: dict, fignum: dict, doc: "Doc" = None) -> str:
    t = b["t"]
    if t == "chapter":
        return f'<h1 class="chapter"><span class="num">فصل {esc(b["n"])}</span>{esc(b["x"])}</h1>'
    if t == "sec":
        lvl = min(b["d"], 4)
        return f'<h{lvl}><span class="hdr-id">{esc(b["label"])}</span> — {esc(b["x"])}</h{lvl}>'
    if t == "appendix":
        return f'<h1 class="chapter"><span class="num">ضمائم</span>{esc(b["x"])}</h1>'
    if t == "table":
        body = render_table(b, fignum)
        if b["wide"]:
            return f'<div class="wide">{body}</div>'
        return body
    if t == "figure":
        img = fignum_img(doc.book, b["id"])
        have = bool(img)
        conf = ""
        if have:
            conf = '<span class="conf">برچسب داده و شمارهٔ جدول منبع، درون خودِ نمودار درج شده است</span>'
        else:
            stats_ref["ph"] += 1
            img = (
                '<div class="box"><b>شکل در این نسخه رسم نشده است</b>'
                'دادهٔ عددیِ متناظر در متن موجود است اما هنوز به نمودار تبدیل نشده.<br>'
                'شمارهٔ شکل و عنوان آن برای پیگیری حفظ شده است.</div>'
            )
        cls = "" if have else "placeholder"
        return (
            f'<figure class="{cls}">'
            f'{img}<figcaption><span class="tno">شکل {esc(b["id"])}</span> — {esc(b["x"])}'
            f'{(" " + esc(b["desc"])) if b.get("desc") else ""}{conf}</figcaption></figure>'
        )
    if t == "formula":
        if "id" in b:
            return (
                f'<div class="formula"><span class="fid">{esc(b["id"])}</span>'
                f'{esc(b["x"])}</div>'
            )
        return f'<div class="formula">{esc(b["x"])}</div>'
    if t == "src":
        return f'<p class="src">{esc(b["x"])}</p>'
    if t == "figdesc":
        return f'<p class="note">{esc(b["x"])}</p>'
    if RE_BOXART.search(b["x"]):
        # کادرهای ASCII (فلوچارت و نمودار متنی) نباید در چاپ مچاله شوند
        return f'<pre class="boxart">{esc(b["x"])}</pre>'
    return f"<p>{esc(b['x'])}</p>"


stats_ref = {"ph": 0}


def fignum_img(book: str, fid: str):
    key = f"{book}__{fid}"
    if os.path.exists(os.path.join(HERE, "figures", key + ".png")):
        return f'<img src="../figures/{esc(key)}.png" alt="">'
    return ""


def build_html(doc: Doc) -> str:
    stats_ref["ph"] = 0
    fignum = {b["id"]: b for b in doc.body if b["t"] == "figure"}

    cover_key = doc.cover.get("کد سند", os.path.splitext(doc.name)[0])
    meta = []
    for k in ("نسخه", "کد سند", "تاریخ تدوین", "متولی"):
        if doc.cover.get(k):
            meta.append(f"<span>{esc(k)}: <b>{esc(doc.cover[k])}</b></span>")

    parts = [
        "<!DOCTYPE html><html lang=fa dir=rtl><head><meta charset=utf-8>",
        f"<title>{esc(doc.name)}</title>",
        '<link rel=stylesheet href="../book.css"></head><body>',
        '<section class="cover">',
        f'<div class="code">{esc(cover_key)}</div>',
        f"<h1>{esc(os.path.splitext(doc.name)[0])}</h1>",
        '<div class="sub">مجموعهٔ اسناد فنی طرح هیدروما نوژین</div>',
        f'<div class="meta">{"".join(meta)}</div>',
        '<div class="warn"><b>وضعیت سند</b>'
        "این نسخه برای بازبینی فنی و چاپ آماده شده است. ارقام مالی آن هنوز "
        "بازنشسته‌نشده‌اند و پیش از انتشار بیرونی باید در سند مرجع واحد تثبیت شوند."
        "</div>",
        "</section>",
    ]

    if doc.toc:
        parts.append('<section class="toc"><h2>فهرست مطالب</h2><ol>')
        for n, title in doc.toc:
            parts.append(f'<li><span class="hdr-id">{esc(n)}</span> — {esc(title)}</li>')
        parts.append("</ol></section>")

    for b in doc.front:
        parts.append(render_block(b, fignum, doc))

    for b in doc.body:
        parts.append(render_block(b, fignum, doc))

    parts.append("</body></html>")
    return "\n".join(parts), stats_ref["ph"]


BOOKLET_FILES = [
    "راهبردی هیدروما.txt", "مهندسی هیدروما.txt", "سند مرجع.txt",
    "توجیهی فنی اقتصادی.txt", "راهنمای نقشه برداری.txt",
] + [f for f in sorted(os.listdir(BOOKS)) if f.startswith("HP-") and f.endswith(".txt")]


def load(path: str) -> Doc:
    return Doc(path).parse()
