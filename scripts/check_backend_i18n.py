#!/usr/bin/env python3
"""Check UI key coverage per language in backend i18n dictionaries."""

import re
import sys


def parse_blocks(src: str) -> dict:
    """Parse 'lang': { 'key': 'value', ... } blocks from an i18n python file."""
    blocks = {}
    for m in re.finditer(r'^\s{0,8}"([a-z]{2})"\s*:\s*\{', src, re.M):
        lang = m.group(1)
        start = m.end()
        depth = 1
        i = start
        while depth > 0 and i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        body = src[start : i - 1]
        keys = re.findall(r'"(\w+)"\s*:', body)
        blocks[lang] = keys
    return blocks


def main(path: str):
    src = open(path, encoding="utf-8").read()
    blocks = parse_blocks(src)
    if not blocks:
        print(f"{path}: no blocks found")
        return
    en_keys = set(blocks.get("en", [])) or set(max(blocks.values(), key=len))
    fa_keys = set(blocks.get("fa", []))
    ref = en_keys | fa_keys
    print(f"\n=== {path} ===")
    print(f"reference keys (fa|en union): {len(ref)}")
    for lang, keys in blocks.items():
        ks = set(keys)
        missing = ref - ks
        extra = ks - ref
        status = "OK" if not missing else "MISSING"
        print(f"  {lang}: keys={len(ks)} missing={len(missing)} extra={len(extra)} -> {status}")
        if missing:
            print(f"    missing: {', '.join(sorted(missing))}")
        if extra:
            print(f"    extra: {', '.join(sorted(extra))}")


for p in sys.argv[1:]:
    main(p)
