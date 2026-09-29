# read-only: print full lines for given 1-based line numbers
import io, sys
P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
with io.open(P, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")
nums = []
for a in sys.argv[1:]:
    if "-" in a:
        s, e = a.split("-"); nums.extend(range(int(s), int(e) + 1))
    else:
        nums.append(int(a))
for n in nums:
    if 1 <= n <= len(lines):
        print(f"L{n}| {lines[n-1]}")
    else:
        print(f"L{n}| <<OUT OF RANGE>>")
