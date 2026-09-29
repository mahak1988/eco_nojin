# read-only occurrence map for راهبردی هیدروما.txt
import sys, io, re

P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
with io.open(P, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

print("TOTAL_LINES", len(lines))
print("=" * 70)

TARGETS = {
    "BC19": "۱٫۹",
    "BC23": "۲٫۳",
    "IRR22": "۲۲٪",
    "IRR22a": "۲۲ درصد",
    "IRR22b": "۲۲٪",
    "PB35": "۳٫۵",
    "NPV957": "۹۵۷",
    "ES805": "۸۰۵",
    "AREA": "۵۶۸٬۰۰۰",
    "AREA2": "۵۶۸۰۰۰",
    "CARB5": "۵ دلار",
    "TANHA": "تنها راهکار",
    "MOVAQE": "موقعیت رقابتی",
    "PCT100": "۱۰۰٪",
    "PCT100w": "۱۰۰ درصد",
    "V10": "سند مرجع v1.0",
    "V10b": "v1.0",
    "AC71": "۷٫۱",
    "WEAP2023": "۲۰۲۳",
    "HYD50": "۵٫۰",
}

for name, needle in TARGETS.items():
    hits = []
    for i, ln in enumerate(lines, 1):
        if needle in ln:
            hits.append(i)
    print(f"{name!r:12} needle={needle!r:22} count={len(hits):4}  lines={hits[:60]}")

print("=" * 70)
# character gate
bad = {
    "CJK": r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]",
    "CYRILLIC": r"[\u0400-\u04ff]",
    "KATAKANA": r"[\u30a0-\u30ff\u31f0-\u31ff]",
    "HANGUL": r"[\uac00-\ud7af\u1100-\u11ff]",
    "HALFWIDTH": r"[\uff00-\uffef]",
    "FFFD": r"\ufffd",
    "NUL": r"\x00",
}
tot = 0
for name, rx in bad.items():
    hh = []
    for i, ln in enumerate(lines, 1):
        m = re.findall(rx, ln)
        if m:
            hh.append((i, m, ln.strip()[:90]))
    tot += len(hh)
    print(f"GATE {name:10} count={len(hh)}")
    for i, m, s in hh[:12]:
        print(f"    L{i}: {m}  ::  {s}")
print("GATE_TOTAL", tot)
