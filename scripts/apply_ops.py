"""Verified exact-substring editor for the booklet sweep.

Reads a JSON array of operations from stdin (or from a file passed as argv[1]).
Each operation is {"find": <exact substring>, "repl": <replacement>} and the
substring must occur exactly once in the whole file, so operations survive the
line drift caused by multi-line insertions. An operation may carry "n" to
restrict the match to one 1-based line. Nothing is written unless every
operation verifies, so a failed anchor never corrupts the booklet.
"""

import json
import sys

PATH = r"D:\eco_nojin\کتابها\HP-16 پایداری شیب.txt"
BANNED = ("فاقد شناسه", "تأییدنشده", "نیازمند خط پایه")


def main() -> int:
    with open(sys.argv[1], encoding="utf-8") as _fh:
        raw = _fh.read() if len(sys.argv) > 1 else sys.stdin.read()
    ops = json.loads(raw)
    with open(PATH, encoding="utf-8") as _fh:
        text = _fh.read()
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(eol)

    errors = []
    staged = list(lines)
    for idx, op in enumerate(ops, 1):
        find, repl, n = op["find"], op["repl"], op.get("n")
        nth = op.get("nth")
        if n is not None and nth is not None:
            # replace only the nth occurrence of `find` on line n
            if not (1 <= n <= len(staged)):
                errors.append(f"op{idx} L{n}: line out of range (file has {len(staged)})")
                continue
            line = staged[n - 1]
            if line.count(find) < nth:
                errors.append(
                    f"op{idx} L{n}: occurrence {nth} of {find} not present\n  LINE: {line}"
                )
                continue
            pos, seen = -1, 0
            while seen < nth:
                pos = line.index(find, pos + 1)
                seen += 1
            staged[n - 1] = line[:pos] + repl + line[pos + len(find) :]
            continue
        if n is not None:
            if not (1 <= n <= len(staged)):
                errors.append(f"op{idx} L{n}: line out of range (file has {len(staged)})")
                continue
            hits = staged[n - 1].count(find)
            if hits != 1:
                errors.append(
                    f"op{idx} L{n}: anchor found {hits} times\n"
                    f"  FIND: {find}\n  LINE: {staged[n - 1]}"
                )
                continue
            staged[n - 1] = staged[n - 1].replace(find, repl)
            continue
        total = sum(line.count(find) for line in staged)
        if op.get("all"):
            if total < 1:
                errors.append(f"op{idx}: anchor not found\n  FIND: {find}")
                continue
        elif total != 1:
            errors.append(f"op{idx}: anchor found {total} times in file\n  FIND: {find}")
            continue
        if op.get("all"):
            staged = [line.replace(find, repl) for line in staged]
            continue
        for i, line in enumerate(staged):
            if find in line:
                staged[i] = line.replace(find, repl)
                break

    if errors:
        print("ABORTED — no write performed")
        for e in errors:
            print(e)
        return 1

    out = eol.join(staged)
    with open(PATH, "w", encoding="utf-8", newline="") as _fh:
        _fh.write(out)
    after = {k: out.count(k) for k in BANNED}
    before = {k: text.count(k) for k in BANNED}
    print(f"OK  ops={len(ops)}  physical_lines={out.count(chr(10)) + 1}")
    for k in BANNED:
        print(f"  {k}: {before[k]} -> {after[k]}   (-{before[k] - after[k]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
