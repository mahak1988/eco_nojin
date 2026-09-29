# read-only normalized occurrence map for راهبردی هیدروما.txt
import io, re

P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
with io.open(P, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

def norm(s):
    return s.replace("٫", ".").replace("٬", "").replace("،", "")

nlines = [norm(l) for l in lines]

def find(pat, rx=False):
    hits = []
    c = re.compile(pat) if rx else None
    for i, ln in enumerate(nlines, 1):
        if (c.search(ln) if rx else (pat in ln)):
            hits.append(i)
    return hits

SETS = [
    ("BC 1.9",   r"۱\.۹"),
    ("BC 2.3",   r"۲\.۳"),
    ("IRR 22",   r"۲۲\s*[٪%]"),
    ("IRR 22wd", r"۲۲\s*(?:درصد|درصدی)"),
    ("PB 3.5",   r"۳\.۵"),
    ("NPV 957",  r"۹۵۷"),
    ("ES 805",   r"۸۰۵"),
    ("AREA 568", r"۵۶۸[,\s]?(?:۰۰۰|۴۰۰|هزار)"),
    ("CARBON 5", r"۵\s*(?:دلار|USD|\$)\s*(?:بر|/|به)\s*(?:هر\s*)?(?:تن|تن\s*CO2|تن\s*کربن)"),
    ("v1.0",     r"v1\.0"),
]
for name, pat in SETS:
    h = find(pat, rx=True)
    print(f"{name:12} count={len(h):4}  {h[:70]}")
print("=" * 70)
# every line mentioning B/C ratio words
for i, ln in enumerate(lines, 1):
    if "منفعت به هزینه" in ln or "B/C" in ln:
        print(f"BCl {i}: {ln.strip()[:150]}")
print("=" * 70)
for i, ln in enumerate(lines, 1):
    if "بازگشت" in ln and ("سال" in ln):
        print(f"PB {i}: {ln.strip()[:150]}")
