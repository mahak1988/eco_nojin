# read-only: dump codepoints of a line
import io, sys
P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
with io.open(P, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")
n = int(sys.argv[1])
ln = lines[n - 1]
print(repr(ln))
print("---")
for i, ch in enumerate(ln):
    if ord(ch) > 0x7F and not (0x0600 <= ord(ch) <= 0x06FF):
        print(i, hex(ord(ch)), repr(ch))
