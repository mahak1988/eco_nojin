import io, re

P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
raw = io.open(P, "rb").read()
L = raw.decode("utf-8").split("\n")
# body = everything before the final correction section (which legitimately quotes old values)
START = next(i for i, l in enumerate(L) if l.startswith("بخش پایانی"))
BODY = L[:START]
print("TOTAL LINES      :", len(L))
print("BODY LINES       :", len(BODY))
print("CORRECTION START : line", START + 1)
print("LAST LINE        :", L[-1])
print()

print("=" * 74)
print("STALE VALUES IN BODY (excl. correction section) — must be ZERO")
print("=" * 74)
stale = {
    "B/C 1.9 with B/C ctx": r"(?:B/C|\u0646\u0633\u0628\u062a \u0645\u0646\u0627\u0641\u0639)[^\n]{0,40}\u06f1[.\u066b]\u06f9",
    "B/C 2.3 with B/C ctx": r"(?:B/C|\u0646\u0633\u0628\u062a \u0645\u0646\u0627\u0641\u0639)[^\n]{0,40}\u06f2[.\u066b]\u06f3",
    "IRR 22 %": r"IRR[^\n]{0,25}\u06f2\u06f2\s*%|\u0646\u0631\u062e \u0628\u0627\u0632\u062f\u0647 \u062f\u0627\u062e\u0644\u06cc[^\n]{0,25}\u06f2\u06f2\s*%",
    "payback 3.5 yr": r"\u06f3[.\u066b]\u06f5\s*\u0633\u0627\u0644",
    "NPV 957": r"\u06f9\u06f5\u06f7",
    "ES 805": r"\u06f8\u06f0\u06f5",
    "area 568,000": r"\u06f5\u06f6\u06f8[\u066c,]\s?[\u06f0\u06f9]{3}|\u06f5\u06f6\u06f8K|\u06f5\u06f6\u06f8 \u0647\u0632\u0627\u0631 \u0647\u06a9\u062a\u0627\u0631",
    "carbon 5 $/t": r"\u06f5\s*\u062f\u0644\u0627\u0631\s*(?:\u0628\u0647|[\u0628\u0631/])\s*(?:\u0647\u0631\s*)?\u062a\u0646",
    "mandrige v1.0": r"\u0633\u0646\u062f \u0645\u0631\u062c\u0639[^\n]{0,30}v1\.0",
    "AquaCrop 7.1": r"AquaCrop[^\n]{0,20}\u06f7[.\u066b]\u06f1",
    "WEAP 2023": r"WEAP[^\n]{0,25}\u06f2\u06f0\u06f2\u06f3",
    "HYDRUS 5.0": r"HYDRUS[^\n]{0,25}\u06f5[.\u066b]\u06f0(?!\u06f6)",
    "26 charts claim": r"\u06f2\u06f6\s*\u0646\u0645\u0648\u062f\u0627\u0631",
    "tornado chart": r"\u0646\u0645\u0648\u062f\u0627\u0631 \u062a\u0648\u0646\u0627\u062f\u0648",
    "radar chart": r"\u0646\u0645\u0648\u062f\u0627\u0631 \u0631\u0627\u062f\u0627\u0631",
    "SDG 90% align": r"\u06f9\u06f0[\u066a%]\s*\u0647\u0645\u0633\u0648\u06cc\u06cc|90\s*%?\s*\u0647\u0645\u0633\u0648\u06cc\u06cc",
}
ok = True
for k, v in stale.items():
    hits = [(i, l.strip()[:105]) for i, l in enumerate(BODY, 1) if re.search(v, l)]
    if hits:
        ok = False
    print(f"  {k:24} {len(hits):3}  {hits[:2]}")
print("  ALL CLEAR" if ok else "  >>> REVIEW NEEDED")
print()

print("=" * 74)
print("BANNED PHRASES IN BODY — must be ZERO")
print("=" * 74)
banned = {
    "\u062a\u0646\u0647\u0627 \u0631\u0627\u0647\u06a9\u0627\u0631 (تنها راهکار)": r"\u062a\u0646\u0647\u0627 \u0631\u0627\u0647\u06a9\u0627\u0631",
    "موقعیت رقابتی (claim)": r"\u0645\u0648\u0642\u0639\u06cc\u062a \u0631\u0642\u0627\u0628\u062a\u06cc\s*(?:\u0645\u0637\u0644\u0648\u0628|\u0642\u0648\u06cc|\u0645\u0646\u062d\u0635\u0635|\u0642\u0648\u06cc\u062a\u06cc)",
    "مطابقت کامل": r"\u0645\u0637\u0627\u0628\u0642\u062a \u06a9\u0627\u0645\u0644",
    "۱۰۰٪ با استاندارد": r"\u06f1\u06f0\u06f0\s*%?\s*\u0628\u0627 \u0627\u0633\u062a\u0627\u0646\u062f\u0627\u0631\u062f",
    "بالاتر از استاندارد": r"\u0628\u0627\u0644\u0627\u062a\u0631 \u0627\u0632 \u0627\u0633\u062a\u0627\u0646\u062f\u0627\u0631\u062f",
    "بازدهی ۱۰۰٪": r"\u0628\u0627\u0632\u062f\u0647\u06cc\s*\u06f1\u06f0\u06f0",
    "نتیجه میدانی": r"\u0646\u062a\u06cc\u062c\u0647 \u0645\u06cc\u062f\u0627\u0646\u06cc",
    "همه پایلوت": r"\u0647\u0645\u0647 \u067e\u0627\u06cc\u0644\u0648\u062a",
    "به دلیل ریسک حذف": r"\u0628\u0647 \u062f\u0644\u06cc\u0644 \u0631\u06cc\u0633\u06a9 \u062d\u0630\u0641",
    "فاقد شناسه": r"\u0641\u0627\u0642\u062f \u0634\u0646\u0627\u0633\u0647",
    "تأییدنشده": r"\u062a\u0623\u06cc\u062f\u0646\u0634\u062f\u0647",
    "نیازمند خط پایه": r"\u0646\u06cc\u0627\u0632\u0645\u0646\u062f \u062e\u0637 \u067e\u0627\u06cc\u0647",
    "ثبت‌نشده در HDR": r"\u062b\u0628\u0629?\u200c?\u0646\u0634\u062f\u0647 \u062f\u0631 HDR",
    "VERDICT/judgement words": r"(?:بی\u200cدفاع|\u0642\u0627\u0636\u0644\u0647?\s+\u0628\u0627\u0637\u0644|\u0633\u0627\u062e\u062a\u0647\u200cای\u0646\u06cc \u0627\u0635\u0648\u0644\u06cc)",
}
ok2 = True
for k, v in banned.items():
    hits = [(i, l.strip()[:100]) for i, l in enumerate(BODY, 1) if re.search(v, l)]
    if hits:
        ok2 = False
    print(f"  {k:32} {len(hits):3}  {hits[:2]}")
print("  ALL CLEAR" if ok2 else "  >>> REVIEW NEEDED")
print()

print("=" * 74)
print("REGISTER VALUES PRESENT IN BODY")
print("=" * 74)
req = {
    "FN-21 2.2193": r"\u06f2\u066b\u06f2\u06f1\u06f9\u06f3",
    "FN-24 3.8235": r"\u06f3\u066b\u06f8\u06f2\u06f3\u06f5",
    "FN-25 4.0263": r"\u06f4\u066b\u06f0\u06f2\u06f6\u06f3",
    "FN-28 102.34": r"\u06f1\u06f0\u06f2\u066b\u06f3\u06f4",
    "FN-23 4.63": r"\u06f4\u066b\u06f6\u06f3",
    "FN-22 439.306": r"\u06f4\u06f3\u06f9\u066b\u06f3\u06f0\u06f6",
    "ES-07 629.95": r"\u06f6\u06f2\u06f9\u066b\u06f9\u06f5",
    "ES-16 87.95": r"\u06f8\u06f7\u066b\u06f9\u06f5",
    "CB-01 3.518": r"\u06f3\u066b\u06f5\u06f1\u06f8",
    "CB-02 25": r"CB-02",
    "SC-03 568,400": r"\u06f5\u06f6\u06f8\u066c\u06f4\u06f0\u06f0",
    "ES-08 358.06": r"\u06f3\u06f5\u06f8\u066b\u06f0\u06f6",
    "v2.0": r"v2\.0",
    "MD-04 7.3": r"\u06f7\u066b\u06f3",
    "MD-05 2025.0": r"\u06f2\u06f0\u06f2\u06f5\u066b\u06f0",
    "MD-07 5.06": r"\u06f5\u066b\u06f0\u066b\u06f6",
    "غیرمیدانی label": r"\u063a\u06cc\u0631\u0645\u06cc\u062f\u0627\u0646\u06cc",
}
for k, v in req.items():
    n = sum(len(re.findall(v, l)) for l in BODY)
    print(f"  {k:20} {n}")
print()

print("=" * 74)
print("100% OCCURRENCES — categorised")
print("=" * 74)
allowed = r"(?:\u062c\u0645\u0639|\u0645\u062c\u0645\u0648\u0639|\u0634\u0631\u06a9\u0627\u0646\u06cc|\u062f\u0627\u0633\u0647|\u0631\u0633\u0645|\u0646\u0633\u0628\u062a|\u0628\u0631\u0627\u06a9\u0646\u062f|\u0648\u0627\u0631\u06cc|WEI|EPI|\u0641\u0642\u0637|\u06a9\u0631\u0628\u0646|\u0627\u0646\u062a\u0642\u0627\u0644|\u062a\u0648\u0644\u06cc\u062f|\u06a9\u0627\u0631\u0627\u06af\u0631|\u062d\u0630\u0641)"
tot = 0
viol = []
for i, l in enumerate(BODY, 1):
    for m in re.finditer(r"\u06f1\u06f0\u06f0\s*%", l):
        tot += 1
        ctx = l[max(0, m.start() - 100): m.end() + 70]
        if not re.search(allowed, ctx):
            viol.append((i, ctx.replace("\t", " | ")))
print("  total 100% in body :", tot)
print("  unclassified        :", len(viol))
for i, c in viol:
    print("    L%d| %s" % (i, c))
