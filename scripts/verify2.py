import io, re
P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
raw = io.open(P, "rb").read()
L = raw.decode("utf-8").split("\n")
print("LINES (split)  :", len(L))
print("ends with \\n   :", raw.endswith(b"\n"))
ne = [i for i, l in enumerate(L, 1) if l.strip()]
print("last non-empty : L%d = %s" % (ne[-1], L[ne[-1] - 1]))
print("trailing blanks:", len(L) - ne[-1])
print()
print("HYDRUS ver     :", [l.strip()[:80] for l in L if "HYDRUS (نسخه" in l])
print("AquaCrop ver   :", [l.strip()[:80] for l in L if "AquaCrop (نسخه" in l])
print("WEAP ver       :", [l.strip()[:80] for l in L if "WEAP (نسخه" in l])
print()
print("--- 100% (Arabic percent U+066A) in body ---")
START = next(i for i, l in enumerate(L) if l.startswith("بخش پایانی"))
BODY = L[:START]
allowed = (r"(?:\u062c\u0645\u0639|\u0645\u062c\u0645\u0648\u0639|\u0634\u0631\u06a9\u0627\u0646\u06cc|\u062f\u0627\u0633\u0647|\u0631\u0633\u0645|\u0646\u0633\u0628\u062a|\u0628\u0631\u0627\u06a9\u0646\u062f|\u0648\u0627\u0631\u06cc|WEI|EPI|\u0641\u0642\u0637|\u06a9\u0631\u0628\u0646|\u0627\u0646\u062a\u0642\u0627\u0644|\u062a\u0648\u0644\u06cc\u062f|\u06a9\u0627\u0631\u0627\u06af\u0631|\u062d\u0630\u0641)")
tot = 0
viol = []
for i, l in enumerate(BODY, 1):
    for m in re.finditer("\u06f1\u06f0\u06f0\s*[\u066a%]", l):
        tot += 1
        ctx = l[max(0, m.start() - 100): m.end() + 80]
        if not re.search(allowed, ctx):
            viol.append((i, ctx.replace("\t", " | ")))
print("total 100%% in body:", tot)
print("unclassified       :", len(viol))
for i, c in viol:
    print("  L%d| %s" % (i, c))
print()
print("--- judgement/verdict probe ---")
for pat in ["\u0628\u06cc\u200c\u062f\u0641\u0627\u0639", "\u0633\u0627\u062e\u062a\u06af\u0627\u0646", "\u0642\u0627\u0636\u0644", "\u0628\u0627\u0637\u0644 \u0627\u0633\u062a"]:
    hits = [(i, l.strip()[:90]) for i, l in enumerate(BODY, 1) if re.search(pat, l)]
    print("  %-14s %d %s" % (pat.replace("\\u", ""), len(hits), hits[:2]))
