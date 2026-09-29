"""Cell-level dead-end sweeper for the HP-16 booklet.

Operates on the tab-delimited rows of the booklet's tables. For each rule the
row is located by its first cell (exact match) inside a line range, and one cell
is addressed either by index or by its current value. That avoids hand-typing
ZWNJ-bearing anchors, which fail silently in most editors.

Rules are read from a JSON file: {"start": int, "end": int, "rules": [
  {"key": "<first cell>", "cell": <index> | "last" | "all", "old": "<current value>",
   "new": "<replacement>", "count": <expected matches, default 1>}
]}
Nothing is written unless every rule verifies.
"""
import json
import sys

PATH = r"D:\eco_nojin\کتابها\HP-16 پایداری شیب.txt"
BANNED = ("فاقد شناسه", "تأییدنشده", "نیازمند خط پایه")


def norm(s: str) -> str:
    """Normalise for key matching: drop ZWNJ and collapse whitespace.

    Persian text in this corpus puts U+200C inside words, and a hand-typed
    anchor that omits it will never match. Normalising both sides makes the
    row lookup immune to that class of silent failure.
    """
    return s.replace("\u200c", "").strip()


def main() -> int:
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    text = open(PATH, encoding="utf-8").read()
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)
    lo, hi = spec["start"], spec["end"]

    errors = []
    staged = list(lines)
    done = 0
    for idx, rule in enumerate(spec["rules"], 1):
        key, new = norm(rule["key"]), rule["new"]
        want = rule.get("count", 1)
        which = rule.get("nth", 1)
        hit = 0
        for i in range(lo - 1, min(hi, len(staged))):
            if rule.get("at") and i + 1 != rule["at"]:
                continue
            if rule.get("atlist") and (i + 1) not in rule["atlist"]:
                continue
            cells = staged[i].split("\t")
            if not cells or (key != "*" and norm(cells[0]) != key):
                continue
            if not rule.get("at") and not rule.get("atlist") and hit + 1 != which:
                hit += 1
                continue
            hit += 1
            if rule.get("col") is not None:
                j = rule["col"]
                if j < len(cells) and cells[j] == rule.get("old", cells[j]):
                    cells[j] = new
                    staged[i] = "\t".join(cells)
                continue
            if rule.get("old") is not None:
                for j, c in enumerate(cells):
                    if c == rule["old"]:
                        cells[j] = new
                        staged[i] = "\t".join(cells)
                        break
            else:
                j = rule["cell"]
                if j == "last":
                    j = len(cells) - 1
                elif j == "all":
                    cells = [new if c in BANNED else c for c in cells]
                    staged[i] = "\t".join(cells)
                    continue
                cells[j] = new
                staged[i] = "\t".join(cells)
                hit += 1
                break
        if hit != want:
            errors.append(
                f"rule{idx} key={key!r}: matched {hit} rows, expected {want}\n"
                f"  LINE: {staged[min(hi, len(staged)) - 1][:160]}"
            )
        done += hit

    if errors:
        print("ABORTED — no write performed")
        for e in errors:
            print(e)
        return 1

    out = eol.join(staged)
    open(PATH, "w", encoding="utf-8", newline="").write(out)
    print(f"OK rows_rewritten={done} physical_lines={out.count(chr(10)) + 1}")
    before = {k: text.count(k) for k in BANNED}
    after = {k: out.count(k) for k in BANNED}
    for k in BANNED:
        print(f"  {k}: {before[k]} -> {after[k]}   (-{before[k] - after[k]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
