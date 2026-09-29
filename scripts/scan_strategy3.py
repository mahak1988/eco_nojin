# read-only precise scan for area / carbon / version / model strings
import io, re
P = r"D:\eco_nojin\کتابها\راهبردی هیدروما.txt"
with io.open(P, "r", encoding="utf-8") as f:
    lines = f.read().split("\n")

def show(title, pat, rx=True, full=False):
    c = re.compile(pat)
    print("#" * 20, title, "#" * 20)
    for i, ln in enumerate(lines, 1):
        if c.search(ln):
            print(f"L{i}| {ln.strip()}" if full else f"L{i}| {ln.strip()[:170]}")

show("AREA-568000", r"۵۶۸[٬,]\s?۰۰۰")
show("AREA-568-thousand-ha", r"۵۶۸\s*(?:هزار|K|٬|,)?\s*هکتار|۵۶۸K|۵۶۸\s?هزار\s?هکتار")
show("AREA-568-other", r"۵۶۸(?![\d٬,.٫])")
show("CARBON-5", r"۵\s*(?:دلار|USD|\$)")
show("CARBON-2050", r"۲۰۵۰|۲۰۵۰\s*دلار")
show("V10", r"v1\.0")
show("MODEL-VER", r"AquaCrop|WEAP|HYDRUS|SWAT\+|RUSLE|RothC|HEC-RAS|۷\.۱|۵\.۰۶|نسخهٔ\s*[۰-۹0-9.]+")
