import io
P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
L = io.open(P, encoding="utf-8").read().split("\n")
print("TOTAL", len(L))
for i, l in enumerate(L, 1):
    s = l.strip()
    if len(s) < 130 and s[:2] in ("هـ", "پ.", "هـ.") or (len(s) < 130 and s[:2] == "هـ"):
        print("L%d| %s" % (i, s[:120]))
print("--- last 12 lines ---")
for i in range(max(1, len(L) - 12), len(L) + 1):
    print("L%d| %s" % (i, L[i - 1][:120]))
